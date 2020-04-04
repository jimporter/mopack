import os

__all__ = ['this_dir', 'test_data_dir']

this_dir = os.path.abspath(os.path.dirname(__file__))
test_data_dir = os.path.join(this_dir, 'data')
