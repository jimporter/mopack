from unittest import mock, TestCase

from mopack.freezedried import *


def _get_type(type):
    if type == 'derived':
        return Derived
    raise TypeError()


class Base(GenericFreezeDried):
    _type_field = 'type'
    _get_type = _get_type


class Derived(Base):
    type = 'derived'


class TestGenericFreezeDriedType(TestCase):
    def test_dehydrate(self):
        config = Derived().dehydrate()
        self.assertEqual(config, {'type': 'derived'})
        self.assertIsInstance(Base.rehydrate(config), Derived)


class TestFreezeDriedVersion(TestCase):
    class C(FreezeDried):
        _version = 2

        @staticmethod
        def upgrade(config, version):
            return config

    def test_dehydrate(self):
        config = self.C().dehydrate()
        self.assertEqual(config, {'_version': 2})

    def test_rehydrate_same_version(self):
        with mock.patch.object(self.C, 'upgrade') as m:
            self.C.rehydrate({'_version': 2})
            m.assert_not_called()

    def test_rehydrate_upgrade(self):
        with mock.patch.object(self.C, 'upgrade',
                               side_effect=self.C.upgrade) as m:
            self.C.rehydrate({'_version': 1})
            m.assert_called_once()

    def test_rehydrate_invalid_version(self):
        with self.assertRaises(TypeError):
            self.C.rehydrate({'_version': 3})


class TestFreezeDriedFields(TestCase):
    def test_simple(self):
        @FreezeDried.fields(rehydrate={'rehydrate': int}, include={'include'},
                            skip={'skip'}, skip_compare={'skip_compare'})
        class C(FreezeDried):
            pass

        self.assertEqual(C._rehydrate_fields, {'rehydrate': int})
        self.assertEqual(C._include_fields, {'include'})
        self.assertEqual(C._skip_fields, {'skip'})
        self.assertEqual(C._skip_compare_fields, {'skip_compare'})

    def test_non_freezedried(self):
        @FreezeDried.fields(rehydrate={'rehydrate': int}, include={'include'},
                            skip={'skip'}, skip_compare={'skip_compare'})
        class C:
            pass

        self.assertEqual(C._rehydrate_fields, {'rehydrate': int})
        self.assertEqual(C._include_fields, {'include'})
        self.assertEqual(C._skip_fields, {'skip'})
        self.assertEqual(C._skip_compare_fields, {'skip_compare'})

    def test_inherit(self):
        @FreezeDried.fields(rehydrate={'rh_base': int}, include={'i_base'},
                            skip={'s_base'}, skip_compare={'sc_base'})
        class Base(FreezeDried):
            pass

        @FreezeDried.fields(rehydrate={'rehydrate': str}, include={'include'},
                            skip={'skip'}, skip_compare={'skip_compare'})
        class C(Base):
            pass

        self.assertEqual(C._rehydrate_fields, {'rh_base': int,
                                               'rehydrate': str})
        self.assertEqual(C._include_fields, {'i_base', 'include'})
        self.assertEqual(C._skip_fields, {'s_base', 'skip'})
        self.assertEqual(C._skip_compare_fields, {'sc_base', 'skip_compare'})

    def test_multiple_inherit(self):
        @FreezeDried.fields(rehydrate={'rh1_base': int}, include={'i1_base'},
                            skip={'s1_base'}, skip_compare={'sc1_base'})
        class Base1(FreezeDried):
            pass

        @FreezeDried.fields(rehydrate={'rh2_base': str}, include={'i2_base'},
                            skip={'s2_base'}, skip_compare={'sc2_base'})
        class Base2:
            pass

        @FreezeDried.fields(rehydrate={'rehydrate': bool}, include={'include'},
                            skip={'skip'}, skip_compare={'skip_compare'})
        class C(Base1, Base2):
            pass

        self.assertEqual(C._rehydrate_fields, {
            'rh1_base': int, 'rh2_base': str, 'rehydrate': bool
        })
        self.assertEqual(C._include_fields, {'i1_base', 'i2_base', 'include'})
        self.assertEqual(C._skip_fields, {'s1_base', 's2_base', 'skip'})
        self.assertEqual(C._skip_compare_fields, {'sc1_base', 'sc2_base',
                                                  'skip_compare'})
