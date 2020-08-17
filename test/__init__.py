import os
import shutil

__all__ = ['AlwaysEqual', 'this_dir', 'test_data_dir', 'test_stage_dir']

this_dir = os.path.abspath(os.path.dirname(__file__))
test_data_dir = os.path.join(this_dir, 'data')
test_stage_dir = os.path.join(this_dir, 'stage')

# Clear the stage directory for this test run.
if os.path.exists(test_stage_dir):
    shutil.rmtree(test_stage_dir)
os.makedirs(test_stage_dir)


class AlwaysEqual:
    def __eq__(self, rhs):
        return True
