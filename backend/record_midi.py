import time
from datetime import datetime
import json
import os

# Import mido with error handling
try:
    import mido
except ImportError:
    raise ImportError(
        "mido library is required. Install it with: pip install mido python-rtmidi"
    )

# Check for rtmidi backend compatibility
try:
    import rtmidi
    # Try to access API_UNSPECIFIED to check compatibility
    if not hasattr(rtmidi, 'API_UNSPECIFIED'):
        print("Warning: rtmidi version may be incompatible. Try: pip uninstall rtmidi-python && pip install python-rtmidi")
except ImportError:
    pass  # rtmidi is optional, mido can use other backends


def midi_note_to_name(note_number):
    """
    Convert MIDI note number (0-127) to note name (e.g., C4, C#4, D4)
    
    Args:
        note_number: MIDI note number (0-127)
    
    Returns:
        Note name string (e.g., "C4", "C#4", "D4")
    """
    if not isinstance(note_number, int) or note_number < 0 or note_number > 127:
        return "N/A"
    
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (note_number // 12) - 1
    note_name = note_names[note_number % 12]
    return f"{note_name}{octave}"

class SonicPiMidiRecorder:
    def __init__(self, output_dir="."):
        """
        Initialize MIDI recorder for Sonic Pi
        
        Args:
            output_dir: Directory to save MIDI files
        """
        self.output_dir = output_dir
        self.midi_messages = []
        self.start_time = None
        self.last_message_time = None
        
        # Verify MIDI backend is working
        self._check_midi_backend()
    
    def _check_midi_backend(self):
        """Check if MIDI backend is properly configured"""
        try:
            # Try to get input names to verify backend works
            _ = mido.get_input_names()
        except Exception as e:
            error_msg = str(e)
            if 'API_UNSPECIFIED' in error_msg or 'rtmidi' in error_msg.lower():
                raise RuntimeError(
                    "MIDI backend error detected. Please run:\n"
                    "  pip uninstall rtmidi-python rtmidi -y\n"
                    "  pip install python-rtmidi mido\n"
                    f"Original error: {error_msg}"
                )
            else:
                raise RuntimeError(f"MIDI backend error: {error_msg}")
        
    def find_sonic_pi_port(self):
        """
        Find Sonic Pi MIDI output port
        Returns the port name or None if not found
        """
        input_ports = mido.get_input_names()
        
        # Common Sonic Pi MIDI port names (may vary by system)
        sonic_pi_keywords = ['sonic', 'pi', 'loopmidi', 'iac', 'virtual']
        
        for port in input_ports:
            port_lower = port.lower()
            # Check if port name contains any Sonic Pi keywords
            if any(keyword in port_lower for keyword in sonic_pi_keywords):
                return port
        
        # If no specific Sonic Pi port found, return first available port
        if input_ports:
            return input_ports[0]
        
        return None
    
    def list_ports(self):
        """List all available MIDI input ports"""
        print("Available MIDI input ports:")
        ports = mido.get_input_names()
        if not ports:
            print("  No MIDI input ports found")
            return
        
        for i, port in enumerate(ports):
            print(f"  {i}: {port}")
    
    def record_once(self, port_name=None, silence_timeout=2.0, max_duration=60.0):
        """
        Record MIDI from Sonic Pi once and save automatically
        
        Args:
            port_name: MIDI port name (None for auto-detect)
            silence_timeout: Seconds of silence before stopping (default: 2.0)
            max_duration: Maximum recording duration in seconds (default: 60.0)
        
        Returns:
            Path to saved MIDI file or None if failed
        """
        # Auto-detect port if not specified
        if port_name is None:
            port_name = self.find_sonic_pi_port()
            if port_name is None:
                print("Error: No MIDI input port found")
                print("\nAvailable ports:")
                self.list_ports()
                return None
            print(f"Using port: {port_name}")
        else:
            print(f"Using specified port: {port_name}")
        
        self.midi_messages = []
        self.start_time = time.time()
        self.last_message_time = self.start_time
        
        print(f"\nWaiting for MIDI from Sonic Pi...")
        print(f"Recording will stop after {silence_timeout}s of silence or {max_duration}s maximum")
        print("Press Ctrl+C to stop manually\n")
        
        try:
            with mido.open_input(port_name) as inport:
                message_count = 0
                
                while True:
                    current_time = time.time()
                    elapsed = current_time - self.start_time
                    
                    # Check max duration
                    if elapsed > max_duration:
                        print(f"\nMaximum duration ({max_duration}s) reached")
                        break
                    
                    # Check silence timeout
                    time_since_last = current_time - self.last_message_time
                    if message_count > 0 and time_since_last > silence_timeout:
                        print(f"\nSilence timeout ({silence_timeout}s) reached")
                        break
                    
                    # Read MIDI messages
                    for msg in inport.iter_pending():
                        timestamp = current_time - self.start_time
                        self.midi_messages.append({
                            'message': msg,
                            'timestamp': timestamp,
                            'type': msg.type
                        })
                        self.last_message_time = current_time
                        message_count += 1
                        
                        # Print note messages for feedback
                        if msg.type in ['note_on', 'note_off']:
                            note_num = msg.note if hasattr(msg, 'note') else None
                            note_name = midi_note_to_name(note_num) if note_num is not None else 'N/A'
                            velocity = msg.velocity if hasattr(msg, 'velocity') else 'N/A'
                            print(f"[{timestamp:.2f}s] {msg.type}: {note_name} (note={note_num}, velocity={velocity})")
                    
                    time.sleep(0.01)  # Small sleep to avoid CPU overload
                    
        except KeyboardInterrupt:
            print("\n\nRecording stopped by user")
        except Exception as e:
            print(f"\nError during recording: {e}")
            return None
        
        if not self.midi_messages:
            print("\nNo MIDI messages received")
            return None
        
        print(f"\nRecorded {len(self.midi_messages)} MIDI messages")
        
        # Automatically save
        return self.save_as_midi()
    
    def save_as_midi(self, filename=None):
        """
        Save recorded MIDI messages as MIDI file
        
        Args:
            filename: Optional custom filename
        
        Returns:
            Path to saved MIDI file or None if failed
        """
        if not self.midi_messages:
            print("No MIDI data to save")
            return None
        
        # Create MIDI file
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Add MIDI messages to track
        last_time = 0
        ticks_per_second = 480  # Standard MIDI resolution
        
        for entry in self.midi_messages:
            # Calculate delta time in ticks
            delta_seconds = entry['timestamp'] - last_time
            delta_ticks = int(delta_seconds * ticks_per_second)
            
            msg = entry['message'].copy(time=delta_ticks)
            track.append(msg)
            last_time = entry['timestamp']
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sonic_pi_output_{timestamp}.mid"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)
        
        # Save file
        mid.save(filepath)
        print(f"MIDI file saved: {filepath}")
        return filepath
    
    def save_as_json(self, filename=None):
        """
        Save MIDI data as JSON (for debugging)
        
        Args:
            filename: Optional custom filename
        
        Returns:
            Path to saved JSON file or None if failed
        """
        if not self.midi_messages:
            print("No MIDI data to save")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"midi_data_{timestamp}.json"
        
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)
        
        data = []
        for entry in self.midi_messages:
            msg_dict = {
                'timestamp': entry['timestamp'],
                'type': entry['type'],
                'data': entry['message'].dict()
            }
            data.append(msg_dict)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"JSON data saved: {filepath}")
        return filepath


# Convenience function for one-time recording
def record_sonic_pi_midi_once(output_dir=".", port_name=None, silence_timeout=2.0, max_duration=60.0):
    """
    Convenience function to record MIDI from Sonic Pi once
    
    Args:
        output_dir: Directory to save MIDI file
        port_name: MIDI port name (None for auto-detect)
        silence_timeout: Seconds of silence before stopping
        max_duration: Maximum recording duration in seconds
    
    Returns:
        Path to saved MIDI file or None if failed
    """
    recorder = SonicPiMidiRecorder(output_dir=output_dir)
    return recorder.record_once(port_name=port_name, silence_timeout=silence_timeout, max_duration=max_duration)


# Example usage
if __name__ == "__main__":
    recorder = SonicPiMidiRecorder(output_dir=".")
    
    # List available ports
    print("=" * 50)
    recorder.list_ports()
    print("=" * 50)
    
    # Record once from Sonic Pi (auto-detect port)
    saved_file = recorder.record_once(silence_timeout=2.0, max_duration=60.0)
    
    if saved_file:
        print(f"\n✓ Successfully saved MIDI file: {saved_file}")
    else:
        print("\n✗ Failed to record MIDI")