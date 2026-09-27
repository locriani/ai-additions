import unittest

from pricing import bulk_discount, round_price


class Pricing(unittest.TestCase):
    def test_small_order_is_full_price(self):
        self.assertEqual(bulk_discount(2, 5.0), 10.0)

    def test_big_order_is_discounted(self):
        self.assertAlmostEqual(bulk_discount(20, 10.0), 180.0)

    def test_round_price(self):
        self.assertEqual(round_price(3.7), 4)


if __name__ == "__main__":
    unittest.main()
