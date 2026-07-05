import unittest
from generated_message_handler import MessageHandler


class TestSerialization(unittest.TestCase):
    def test_roundtrip(self):
        h = MessageHandler('tester')
        msg = h.make_message(receiver='recv', team='Argentina', probability=0.3456, source='test', timestamp='12345')
        data = h.serialize(msg)
        parsed = h.deserialize(data)
        # core fields
        self.assertEqual(parsed['sender'], 'tester')
        self.assertEqual(parsed['receiver'], 'recv')
        self.assertEqual(parsed['team'], 'Argentina')
        self.assertAlmostEqual(float(parsed['probability']), 0.3456, places=4)


if __name__ == '__main__':
    unittest.main()
