from src.memory.vector_memory import VectorMemory

vm = VectorMemory()

print("Before:", len(vm.questions))

vm.add("customer disconnected call")
vm.add("shipment delayed")
vm.add("customer returned package")

print("After:", len(vm.questions))

print(vm.search("cx cut call"))