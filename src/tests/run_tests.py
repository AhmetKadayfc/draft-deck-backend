import unittest
import sys
from pathlib import Path

# Add the project root directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

if __name__ == "__main__":
    # Discover all tests in the tests directory
    test_suite = unittest.defaultTestLoader.discover('src/tests', pattern='test_*.py')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful()) 