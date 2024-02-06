import unittest

from src.api_bot.api_bot import APIRunner


class MyTestCase(unittest.TestCase):
    def test_empty_arrays(self):
        file = "example_arrays.json"

        runner = APIRunner(None)
        result = runner.arrays_to_set(file)
        self.assertIsNotNone(result)
        # self.assertEqual(, False)  # add assertion here


if __name__ == "__main__":
    unittest.main()
