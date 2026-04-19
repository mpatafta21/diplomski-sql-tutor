"""
SPADE smoke test — provjerava da dva agenta mogu razmijeniti FIPA-ACL poruku
preko Prosody XMPP servera.

Pokreni: uv run python scripts/test_spade.py
"""
import asyncio
import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message


class SenderAgent(Agent):
    class SendBehaviour(OneShotBehaviour):
        async def run(self):
            print(f"[Sender] Šaljem poruku receiver-u...")
            msg = Message(to="evaluator@localhost")
            msg.set_metadata("performative", "inform")
            msg.body = "Hello from Coordinator!"
            await self.send(msg)
            print(f"[Sender] Poruka poslana.")
            await asyncio.sleep(2)
            await self.agent.stop()

    async def setup(self):
        print(f"[Sender] Agent pokrenut: {self.jid}")
        self.add_behaviour(self.SendBehaviour())


class ReceiverAgent(Agent):
    class ReceiveBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                print(f"[Receiver] Primio poruku: '{msg.body}' od {msg.sender}")
                print(f"[Receiver] Performative: {msg.get_metadata('performative')}")
                await self.agent.stop()

    async def setup(self):
        print(f"[Receiver] Agent pokrenut: {self.jid}")
        self.add_behaviour(self.ReceiveBehaviour())


async def main():
    receiver = ReceiverAgent("evaluator@localhost", "eval_pw", port=5222, verify_security=False)
    await receiver.start(auto_register=False)

    sender = SenderAgent("coordinator@localhost", "coord_pw", port=5222, verify_security=False)
    await sender.start(auto_register=False)

    # Čekaj da agenti završe
    await spade.wait_until_finished([sender, receiver])
    print("Test završen.")


if __name__ == "__main__":
    spade.run(main())
