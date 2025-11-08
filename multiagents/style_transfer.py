#!/usr/bin/env python3
"""
style_transfer.py
--------------------------------------
Style transfer for Sonic Pi code using multi-agent system
Based on existing 5 agents with modifications for style transfer:
1. Style Analyzer: Analyzes the original code and style requirements
2. Style Transformer: Transforms the code according to style requirements
3. Style Critic: Reviews the transformed code
4. Style Arranger: Integrates feedback and outputs final code
5. Style Compiler: Compiles to MIDI (optional, can reuse existing compiler)

Usage:
    from style_transfer import style_transfer_sonic_pi
    new_code = style_transfer_sonic_pi(original_code, style_request, client)
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from openai import OpenAI

from v2 import MusicAgent, load_docs_content


def style_transfer_sonic_pi(original_code, style_request, client, log_callback=None):
    """
    Multi-agent style transfer for Sonic Pi code
    
    Args:
        original_code: Original Sonic Pi Ruby code
        style_request: Style transfer request (e.g., "convert to rock style", "make it jazz")
        client: OpenAI client
        log_callback: Optional callback function for logging
    
    Returns:
        Transformed Sonic Pi code
    """
    
    def log(message):
        """Log message to callback or print to console"""
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    # Load docs.txt content
    docs_content = load_docs_content()
    
    # Define agents with style transfer focus
    style_analyzer = MusicAgent(
        "Style Analyzer",
        "Responsible for analyzing the original Sonic Pi code and understanding the style transfer requirements. "
        "Should identify current musical elements (tempo, instruments, dynamics, rhythm patterns) and map them to the target style.",
        client
    )
    
    style_transformer = MusicAgent(
        "Style Transformer",
        "Responsible for transforming Sonic Pi code according to style requirements. "
        "Should modify instruments (use_synth), dynamics (amp, velocity), rhythm patterns, and effects (with_fx) "
        "to match the target style. Sonic Pi uses Ruby syntax, common commands include: play, sample, live_loop, sleep, use_synth, with_fx, etc.",
        client
    )
    
    style_critic = MusicAgent(
        "Style Critic",
        "Responsible for reviewing the style-transformed Sonic Pi code and ensuring it correctly implements the style transfer. "
        "Should verify that instruments, dynamics, and effects match the target style, and that code syntax is correct.",
        client
    )
    
    style_arranger = MusicAgent(
        "Style Arranger",
        "Responsible for integrating feedback into the final style-transformed Sonic Pi code. "
        "Should ensure the code is runnable and correctly implements the style transfer.",
        client
    )
    
    log(f"🎨 Starting style transfer: {style_request}\n")
    log("=" * 60 + "\n")
    
    # Step 1: Style Analyzer - Analyze original code and style requirements
    log("🔍 Step 1: Style Analyzer - Analyzing original code and style requirements...\n")
    
    analyzer_system_prompt = style_analyzer.role_desc
    if docs_content:
        analyzer_system_prompt += f"\n\nSonic Pi Documentation Reference:\n{docs_content[:4000]}"
    
    analyzer_prompt = [
        {"role": "system", "content": analyzer_system_prompt},
        {"role": "user", "content": f"""Analyze the following Sonic Pi code and style transfer request:

Original Sonic Pi Code:
{original_code}

Style Transfer Request:
{style_request}

Please provide a detailed analysis that includes:
1. Current musical elements in the code (tempo, instruments, dynamics, rhythm)
2. Target style characteristics based on the request
3. Required modifications (instruments, effects, dynamics, rhythm patterns)
4. Specific Sonic Pi commands that need to be changed or added

Output your analysis in a clear, structured format."""}
    ]
    
    analysis = style_analyzer.chat(analyzer_prompt)
    log("\n🔍 Style analysis completed.\n")
    log(f"Analysis:\n{analysis}\n")
    log("=" * 60 + "\n")
    
    # Step 2: Style Transformer - Transform the code
    log("🎭 Step 2: Style Transformer - Transforming code according to style requirements...\n")
    
    transformer_system_prompt = style_transformer.role_desc
    if docs_content:
        transformer_system_prompt += f"\n\nSonic Pi Documentation Reference:\n{docs_content[:4000]}"
    
    # Build style transformation guidelines based on common styles
    style_guidelines = build_style_guidelines(style_request)
    
    transformer_prompt = [
        {"role": "system", "content": transformer_system_prompt},
        {"role": "user", "content": f"""Transform the following Sonic Pi code according to the style transfer request:

Original Code:
{original_code}

Style Transfer Request:
{style_request}

Style Analysis:
{analysis}

Style Transformation Guidelines:
{style_guidelines}

Requirements:
1. Modify the code to match the target style
2. Change instruments using use_synth (e.g., :piano, :saw, :prophet, :beep, :sine, :tri, :square, :noise)
3. Adjust dynamics using amp parameter (0.0 to 1.0) or velocity in midi functions
4. Add or modify effects using with_fx (e.g., :reverb, :distortion, :echo, :flanger)
5. Modify rhythm patterns if needed (sleep durations, note patterns)
6. Keep the overall structure and timing similar to the original
7. Output complete runnable code
8. Wrap the code with ```ruby ... ```
9. Use `midi` function to allow MIDI output if not already present"""}
    ]
    
    transformed_draft = style_transformer.chat(transformer_prompt)
    log("\n🎭 Style transformation draft completed.\n")
    log(f"Transformed Draft:\n{transformed_draft}\n")
    log("=" * 60 + "\n")
    
    # Step 3: Style Critic - Review the transformed code
    log("🧐 Step 3: Style Critic - Reviewing transformed code...\n")
    
    critic_prompt = [
        {"role": "system", "content": style_critic.role_desc},
        {"role": "user", "content": f"""Review the following style-transformed Sonic Pi code:

Original Code:
{original_code}

Style Transfer Request:
{style_request}

Transformed Code:
{transformed_draft}

Please review and provide feedback:
1. Does the transformed code correctly implement the style transfer?
2. Are the instruments, dynamics, and effects appropriate for the target style?
3. Are there any syntax errors or issues?
4. What improvements can be made to better match the target style?

Provide specific, actionable feedback."""}
    ]
    
    critic_feedback = style_critic.chat(critic_prompt)
    log("\n🧐 Style critic feedback completed.\n")
    log(f"Critic Feedback:\n{critic_feedback}\n")
    log("=" * 60 + "\n")
    
    # Step 4: Style Arranger - Integrate feedback
    log("🎵 Step 4: Style Arranger - Integrating feedback into final code...\n")
    
    arranger_prompt = [
        {"role": "system", "content": style_arranger.role_desc},
        {"role": "user", "content": f"""Integrate the feedback into the final style-transformed Sonic Pi code:

Original Code:
{original_code}

Style Transfer Request:
{style_request}

Transformed Draft:
{transformed_draft}

Critic Feedback:
{critic_feedback}

Please output the final, complete, runnable Sonic Pi code that:
1. Correctly implements the style transfer
2. Incorporates the critic's feedback
3. Is syntactically correct
4. Is wrapped with ```ruby ... ```"""}
    ]
    
    final_output = style_arranger.chat(arranger_prompt)
    log("\n🎵 Style arranger final code completed.\n")
    log("=" * 60 + "\n")
    
    # Extract Ruby code
    m = re.search(r"```ruby(.*?)```", final_output, re.DOTALL)
    if m:
        transformed_code = m.group(1).strip()
    else:
        # Try to find code without markdown
        m = re.search(r"(live_loop.*?end|use_synth.*?play.*?sleep)", final_output, re.DOTALL)
        if m:
            transformed_code = m.group(0).strip()
        else:
            transformed_code = final_output.strip()
    
    log(f"✅ Style transfer completed!\n")
    log(f"Original code length: {len(original_code)} characters\n")
    log(f"Transformed code length: {len(transformed_code)} characters\n")
    
    return transformed_code


def build_style_guidelines(style_request):
    """
    Build style transformation guidelines based on the style request
    """
    style_lower = style_request.lower()
    guidelines = []
    
    if "rock" in style_lower or "摇滚" in style_request:
        guidelines.append("""
**Rock Style Guidelines:**
- Use aggressive synths: :saw, :prophet, :saw, :square
- Add distortion effect: with_fx :distortion, amp: 0.8 do ... end
- Increase amplitude: amp: 0.8 to 1.0
- Use strong, punchy rhythms
- Add bass lines with lower notes
- Use :reverb and :echo effects for depth
- Consider adding drum samples or patterns
""")
    
    if "jazz" in style_lower or "爵士" in style_request:
        guidelines.append("""
**Jazz Style Guidelines:**
- Use smooth synths: :piano, :sine, :beep
- Add reverb: with_fx :reverb, room: 0.8 do ... end
- Use moderate amplitude: amp: 0.5 to 0.7
- Add swing rhythm patterns (slightly delayed off-beats)
- Use complex chord progressions
- Add :flanger or :chorus effects for richness
- Consider adding multiple layers with different synths
""")
    
    if "soft" in style_lower or "quiet" in style_lower or "轻柔" in style_request or "安静" in style_request:
        guidelines.append("""
**Soft/Quiet Style Guidelines:**
- Use gentle synths: :piano, :sine, :beep
- Reduce amplitude: amp: 0.3 to 0.5
- Add reverb: with_fx :reverb, room: 0.9, damp: 0.8 do ... end
- Use longer note durations (longer sleep times)
- Avoid harsh sounds or distortion
- Use :echo effect for subtle depth
- Keep dynamics gentle and smooth
""")
    
    if "electronic" in style_lower or "电子" in style_request:
        guidelines.append("""
**Electronic Style Guidelines:**
- Use electronic synths: :prophet, :saw, :square, :tri
- Add effects: :reverb, :echo, :flanger, :lpf (low pass filter)
- Use varied amplitude for dynamics
- Add rhythmic patterns with samples
- Consider using :bitcrusher or :slicer effects
- Use syncopated rhythms
""")
    
    if "classical" in style_lower or "古典" in style_request:
        guidelines.append("""
**Classical Style Guidelines:**
- Use piano-like synths: :piano, :sine
- Add reverb: with_fx :reverb, room: 0.7 do ... end
- Use moderate amplitude: amp: 0.5 to 0.7
- Use longer note durations
- Avoid electronic effects
- Focus on melody and harmony
""")
    
    if not guidelines:
        guidelines.append("""
**General Style Guidelines:**
- Modify use_synth to match the target style
- Adjust amp values for appropriate dynamics
- Add with_fx effects to enhance the style
- Modify rhythm patterns if needed
- Keep the overall structure similar to original
""")
    
    return "\n".join(guidelines)


if __name__ == "__main__":
    # Test example
    test_code = """
live_loop :melody do
  use_synth :piano
  play :C4, amp: 0.5
  sleep 0.5
  play :E4, amp: 0.5
  sleep 0.5
  play :G4, amp: 0.5
  sleep 0.5
end
"""
    
    test_style = "convert to rock style"
    
    # Note: This requires a valid OpenAI client
    # client = OpenAI(api_key="your-key", base_url="https://api.deepseek.com")
    # result = style_transfer_sonic_pi(test_code, test_style, client)
    # print(result)

