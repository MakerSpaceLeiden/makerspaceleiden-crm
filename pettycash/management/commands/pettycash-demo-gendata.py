import random
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from members.models import User
from pettycash.models import (
    PettycashReimbursementRequest,
    PettycashSku,
    PettycashTransaction,
)


class Command(BaseCommand):
    help = "Generate some transactions and some reimbursement requests."

    def handle(self, *args, **options):
        skus = PettycashSku.objects.all()
        users = User.objects.all().exclude(id=settings.POT_ID)

        for user in users:
            # Create some payment of a user to the general account for
            # 3 to 5 random items from the price list.
            #
            for i in range(random.randrange(3, 5)):
                sku = random.choice(skus)

                tx = PettycashTransaction(
                    src=user,
                    dst=User.objects.get(id=settings.POT_ID),
                    amount=sku.amount,
                    description=sku.name,
                )
                tx._change_reason = "Auto/random generated."
                tx.save()

                print(tx)

        # Have a couple of users request reimbursement.
        for i in range(5):
            user = random.choice(users)

            rq = PettycashReimbursementRequest(
                src=User.objects.get(id=settings.POT_ID),
                dst=user,
                amount=random.randrange(3, 50),
                description="Replacement %s for the %s"
                % (
                    random.choice(["froeshers", "snoffers", "bralls"]),
                    random.choice(["frell machine", "romph cutter", "persh hammer"]),
                ),
                viaTheBank=(i == 1),
            )
            rq._change_reason = "Auto/random generated."
            rq.save()

            print(rq)

        sys.exit(0)
