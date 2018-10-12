import asyncio
from orchstr8.testcase import IntegrationTestCase, d2f
from torba.constants import COIN


class ReconnectTests(IntegrationTestCase):

    VERBOSE = False

    async def test_connection_drop_still_receives_events_after_reconnected(self):
        await d2f(self.ledger.update_account(self.account))
        address1 = await d2f(self.account.receiving.get_or_create_usable_address())
        self.ledger.network.client.connectionLost()
        sendtxid = await self.blockchain.send_to_address(address1, 1.1337)
        await self.on_transaction_id(sendtxid)  # mempool
        await self.blockchain.generate(1)
        await self.on_transaction_id(sendtxid)  # confirmed

        self.assertEqual(round(await self.get_balance(self.account)/COIN, 4), 1.1337)
        # is it real? are we rich!? let me see this tx...
        d = self.ledger.network.get_transaction(sendtxid)
        # what's that smoke on my ethernet cable? oh no!
        self.ledger.network.client.connectionLost()
        with self.assertRaisesRegex(TimeoutError, 'Connection dropped'):
           await d2f(d)
        # rich but offline? no way, no water, let's retry
        with self.assertRaisesRegex(ConnectionError, 'connection is not available'):
            await d2f(self.ledger.network.get_transaction(sendtxid))
        # * goes to pick some water outside... * time passes by and another donation comes in
        sendtxid = await self.blockchain.send_to_address(address1, 42)
        await self.blockchain.generate(1)
        # omg, the burned cable still works! torba is fire proof!
        await d2f(self.ledger.network.get_transaction(sendtxid))

