from servidor.maquina.maquina import Maquina
from cliente.interface.interface_grafica import InterfaceGrafica
def main():
    print("Executing Main in cliente")
    #maq = Maquina()
    #int = Interface(maq)
    int = InterfaceGrafica()
    int.execute()
if __name__ == '__main__':
    main()
