# from django.test import TestCase
# from django.core.exceptions import ValidationError
#
# from apps.partners.models import Region, Outlet
# from apps.testing.fixtures.pieces.base_structure import create_base_structure
# from apps.testing.fixtures.pieces.users import create_acc_man
#
#
# class OutletTestCase(TestCase):
#     def setUp(self):
#         acc_man = create_acc_man()
#         self.region, self.partner, self.outlet = create_base_structure(acc_man)
#         self.other_region = Region.objects.create(
#             name='other region',
#             acc_man=acc_man
#         )
#
#     def test_update_outlet(self):
#         with self.assertRaises(ValidationError):
#             self.outlet.region = self.other_region
#             self.outlet.save()
#
#     def test_partner_update_region_with_outlet(self):
#         self.partner.region = self.other_region
#         self.partner.save()
#
#         try:
#             self.outlet.region = self.other_region
#             self.outlet.save()
#         except ValidationError:
#             self.fail('При смене региона ТТ на такой-же как и у партнера ошибок не должно быть')
