from django.test import Client, TestCase
from django.conf import settings
from sumup_connector.sumupapi import SumupAPI, SumupError

class SumupAPITests(TestCase):

  def setUp(self):
    pass
        
  def test_auth_fail(self):
    try:
       api = SumupAPI('M123456','sb_12121ABNABSNMASA1')
       lst = api.list_readers()
       self.fail("Should have failed with an unauthorized")
    except SumupError as e:
       self.assertEqual(e.json['status_code'], 401)
       self.assertEqual(e.json['data']['code'], 'unauthorized')
       pass

  def test_auth(self):
    # Silently skip test if not configured.
    if not hasattr(settings,'SUMUP_MERCHANT') or not hasattr(settings,'SUMUP_API_KEY'):
        return

    api = SumupAPI(settings.SUMUP_MERCHANT, settings.SUMUP_API_KEY)
    lst = api.list_readers()

  def test_readers(self):
    # Silently skip test if not configured.
    if not hasattr(settings,'SUMUP_MERCHANT') or not hasattr(settings,'SUMUP_API_KEY'):
        return

    # Check that at least one reader is ours/known to the system
    # if one is configured.
    #
    if not hasattr(settings,'SUMUP_READER'):
        return

    api = SumupAPI(settings.SUMUP_MERCHANT, settings.SUMUP_API_KEY)
    lst = api.list_readers()
    
    for reader in lst:
       if settings.SUMUP_READER == reader['id']:
          if reader['status'] == 'paired':
              # print(f"Reader: {reader['name']} configured ok")
              return
          raise Exception("reader not paired")

    raise Exception("reader not listed")

  def test_txs(self):
    # Silently skip test if not configured.
    if not hasattr(settings,'SUMUP_MERCHANT') or not hasattr(settings,'SUMUP_API_KEY'):
        return

    # Fetch all transactions - and make sure there are at least some
    api = SumupAPI(settings.SUMUP_MERCHANT, settings.SUMUP_API_KEY)
    txs = api.list_transactions()
    n = len(txs)
    self.assertTrue(n > 60)

    # Take a transaction in the middle - and fetch from that point;
    # but not including that transaction.
    #
    mid = int(len(txs)/2)

    txm = txs[mid]
    txi = txm['transaction_id']
    txt = txm['timestamp']

    expected = txs[mid+1:]

    txs2 = api.list_transactions(from_ref=txi)
    nm = len(txs2)

    # All last ones, from, but not including, the middle one.
    self.assertEqual(nm, n - mid - 1)
    self.assertEqual(txs2, expected)
    
    # Same thing - but now from a timestap - so we should get
    # that element this time included in our set.
    # 
    expected = txs[mid:]

    txs2 = api.list_transactions(changes_since =  txt)
    nm = len(txs2)

    # All last ones, from, including, that middle one.
    self.assertEqual(nm, n - mid)
    self.assertEqual(txs2[0], txm)
    self.assertEqual(txs2, expected)

