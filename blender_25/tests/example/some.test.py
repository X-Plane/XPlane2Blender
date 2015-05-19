import unittest

class TestSomething(unittest.TestCase):
    def test_something(self):
        self.assertEqual('foo', 'foo')

suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSomething)
unittest.TextTestRunner().run(suite)
