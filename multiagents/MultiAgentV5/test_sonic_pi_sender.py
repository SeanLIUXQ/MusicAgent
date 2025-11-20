import unittest

import sonic_pi_sender


class FakeOscClient:
    """假客户端，用来拦截并记录 send() 调用，而不是实际发到 Sonic Pi。"""
    def __init__(self):
        self.sent_messages = []

    def send(self, message):
        # 这里 message 是 python-osc 的 OscMessage 实例
        self.sent_messages.append(message)


class TestSonicPiSender(unittest.TestCase):
    def setUp(self):
        # 每个用例前都重置成一个假的 client，避免真的往 4560 发包
        sonic_pi_sender._osc_client = FakeOscClient()

    def test_empty_code_should_not_send_message(self):
        """空代码时不应发送 OSC 消息，并输出提醒日志。"""
        logs = []

        sonic_pi_sender.send_code_to_sonic_pi("   ", log_callback=logs.append)

        # 1. 日志里应该包含“代码为空”字样
        all_logs = "".join(logs)
        self.assertIn("代码为空", all_logs)

        # 2. 不应该调用任何 send
        fake_client = sonic_pi_sender._osc_client
        self.assertEqual(len(fake_client.sent_messages), 0)

    def test_valid_code_should_send_osc_message(self):
        """正常代码应发送一条 /run-code 的 OSC 消息，参数是完整代码字符串。"""
        logs = []
        code = "use_synth :beep\nplay 60"

        sonic_pi_sender.send_code_to_sonic_pi(code, log_callback=logs.append)

        fake_client = sonic_pi_sender._osc_client
        # 1. 应该发送了一条消息
        self.assertEqual(len(fake_client.sent_messages), 1)

        msg = fake_client.sent_messages[0]

        # 2. 消息应是 python-osc 的 OscMessage，并且 address 正确
        from pythonosc.osc_message import OscMessage
        self.assertIsInstance(msg, OscMessage)
        self.assertEqual(msg.address, "/run-code")

        # 3. 参数里应只有一个元素，就是我们传入的 code 字符串
        self.assertEqual(msg.params, [code])

        # 4. 日志里应包含“已通过 OSC 将代码发送到 Sonic Pi”之类的成功提示
        all_logs = "".join(logs)
        self.assertIn("已通过 OSC 将代码发送到 Sonic Pi", all_logs)

    def test_client_send_error_should_be_logged(self):
        """如果底层 client.send 抛异常，函数不崩但会记录错误日志。"""
        class ErrorClient:
            def send(self, message):
                raise RuntimeError("fake send error")

        sonic_pi_sender._osc_client = ErrorClient()
        logs = []

        sonic_pi_sender.send_code_to_sonic_pi("play 60", log_callback=logs.append)

        all_logs = "".join(logs)
        self.assertIn("发送到 Sonic Pi 失败", all_logs)
        self.assertIn("fake send error", all_logs)


if __name__ == "__main__":
    unittest.main()