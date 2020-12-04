from unittest import TestCase

from mopack.freezedried import FreezeDried


class TestFreezeDriedFields(TestCase):
    def test_simple(self):
        @FreezeDried.fields(rehydrate={'rehydrate': int}, skip={'skip'},
                            skip_compare={'skip_compare'})
        class C(FreezeDried):
            pass

        self.assertEqual(C._rehydrate_fields, {'rehydrate': int})
        self.assertEqual(C._skip_fields, {'skip'})
        self.assertEqual(C._skip_compare_fields, {'skip_compare'})

    def test_non_freezedried(self):
        @FreezeDried.fields(rehydrate={'rehydrate': int}, skip={'skip'},
                            skip_compare={'skip_compare'})
        class C:
            pass

        self.assertEqual(C._rehydrate_fields, {'rehydrate': int})
        self.assertEqual(C._skip_fields, {'skip'})
        self.assertEqual(C._skip_compare_fields, {'skip_compare'})

    def test_inherit(self):
        @FreezeDried.fields(rehydrate={'rh_base': int}, skip={'s_base'},
                            skip_compare={'sc_base'})
        class Base(FreezeDried):
            pass

        @FreezeDried.fields(rehydrate={'rehydrate': float}, skip={'skip'},
                            skip_compare={'skip_compare'})
        class C(Base):
            pass

        self.assertEqual(C._rehydrate_fields, {'rh_base': int,
                                               'rehydrate': float})
        self.assertEqual(C._skip_fields, {'s_base', 'skip'})
        self.assertEqual(C._skip_compare_fields, {'sc_base', 'skip_compare'})

    def test_multiple_inherit(self):
        @FreezeDried.fields(rehydrate={'rh1_base': int}, skip={'s1_base'},
                            skip_compare={'sc1_base'})
        class Base1(FreezeDried):
            pass

        @FreezeDried.fields(rehydrate={'rh2_base': str}, skip={'s2_base'},
                            skip_compare={'sc2_base'})
        class Base2:
            pass

        @FreezeDried.fields(rehydrate={'rehydrate': float}, skip={'skip'},
                            skip_compare={'skip_compare'})
        class C(Base1, Base2):
            pass

        self.assertEqual(C._rehydrate_fields, {
            'rh1_base': int, 'rh2_base': str, 'rehydrate': float
        })
        self.assertEqual(C._skip_fields, {'s1_base', 's2_base', 'skip'})
        self.assertEqual(C._skip_compare_fields, {'sc1_base', 'sc2_base',
                                                  'skip_compare'})
