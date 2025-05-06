import importlib

from django.conf import settings
from django.test import TestCase
from moneyed import EUR, Money

from members.models import User
from pettycash.models import PettycashBalanceCache, PettycashTransaction

ic = importlib.import_module("members.management.commands.import-consolidated")
ui = importlib.import_module("members.management.commands.user-init")

pd = importlib.import_module("pettycash.management.commands.pettycash-demo-gendata")
si = importlib.import_module("pettycash.management.commands.pettycash-import-pricelist")
pc = importlib.import_module("pettycash.management.commands.pettycash-recache")


def check():
    balance = Money(0, EUR)
    for user in User.objects.all():
        out = Money(0, EUR)
        for tx in PettycashTransaction.objects.all().filter(src=user):
            out = out + tx.amount

        inc = Money(0, EUR)
        for tx in PettycashTransaction.objects.all().filter(dst=user):
            inc = inc + tx.amount

        ce = PettycashBalanceCache.objects.get(owner=user).balance
        if inc - out != ce:
            return False
        balance += ce
    return balance == Money(0, EUR)


def dump(title):
    print(title)
    print(
        "{:28}: {:8} - {:8} = {:8} == {:8}".format(
            "participant", "in", "out", "balance", "cached"
        )
    )
    balance = Money(0, EUR)
    for user in User.objects.all().order_by("id"):
        out = Money(0, EUR)
        for tx in PettycashTransaction.objects.all().filter(src=user):
            out = out + tx.amount

        inc = Money(0, EUR)
        for tx in PettycashTransaction.objects.all().filter(dst=user):
            inc = inc + tx.amount

        r = inc - out

        ce = " not cached"
        exen = PettycashBalanceCache.objects.all().filter(owner=user)
        if exen:
            ce = exen[0].balance.amount

        name = "{}".format(user.name())
        out = out.amount
        inc = inc.amount
        r = r.amount

        err = ""
        if r != ce:
            err = "****"

        print(f"{name:28}: {inc:8.2f} - {out:8.2f} = {r:8.2f} == {ce:8} {err}")

    balance = balance.amount
    print(f"{balance:72.2f}")


class PettycashTest(TestCase):
    def setUpTestData():
        # We'll move this to some general test setup if we use this in more places (move to setUpTestData, etc)

        if User.objects.all().count() < 1:
            ui.user_init()

        if User.objects.all().count() < 5:
            with open("demo/consolidated.txt", "r") as file:
                ic.import_consolidated([file])

        with open("demo/pricelist.csv", "r") as file:
            si.import_pricelist(0, 0, [file])

        pd.pettycash_generate_demodata()
        dump("Test data")

    def setUp(self):
        self.assertEqual(pc.pettycash_recache(), 0)
        self.assertEqual(check(), True)

    # We should start with a clean /matching cache
    #
    def test_0001(self):
        self.assertEqual(check(), True)

    # Simple transfer
    #
    def test_0002(self):
        user1 = User.objects.get(pk=4)
        user2 = User.objects.get(pk=5)

        tx = PettycashTransaction(
            src=user1, dst=user2, description="test", amount=Money(1, EUR)
        )
        tx._change_reason = "test"
        tx.save(is_privileged=True)

        self.assertEqual(check(), True)

    # Simple transfer to POT
    #
    def test_0003(self):
        user1 = User.objects.get(pk=4)
        user2 = User.objects.get(pk=settings.POT_ID)

        tx = PettycashTransaction(
            src=user1, dst=user2, description="test", amount=Money(1, EUR)
        )
        tx._change_reason = "test"
        tx.save(is_privileged=True)

        self.assertEqual(check(), True)

    # Delete a user
    #
    def test_0004(self):
        user = User.objects.get(pk=7)
        user.delete()
        self.assertEqual(check(), True)
        dump("Post delete of {}".format(user))
