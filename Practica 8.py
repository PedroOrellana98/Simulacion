import tkinter as tk
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections
import random
import simpy
from tkinter import *
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

tiemposAgotados = []
numerosRenegados = []

def generarPDF():
    w, h = A4
    c = canvas.Canvas("Informe Tkinter.pdf", pagesize=A4)
    c.drawString(225, h - 50, "INFORME TKINTER BOLETOS CINE")
    c.drawString(50, h - 80, "Peliculas")
    c.drawString(50, h - 100, str(peliculas))
    c.drawString(50, h - 120, "Tiempo en el que se agoto cada pelicula")
    c.drawString(50, h - 140, str([f"{num:.1f}" for num in tiemposAgotados]))
    c.drawString(50, h - 160, "Numero de personas que salieron de la fila/renegados")
    c.drawString(50, h - 180, str(numerosRenegados))
    c.drawImage("personas_renegadas.png", 50, h - 400, width=300, height=200)
    c.drawImage("tiempo_agotado.png", 50, h - 625, width=300, height=200)
    c.showPage()
    c.save()

root = tk.Tk()

NUM_BOLETO = 50
TIEMPO_SIMULACION = 120


def ventaBoletos(env, num_boletos, pelicula, teatro):
    with teatro.contador.request() as turno:
        resultado = yield turno | teatro.sold_out[pelicula]
        if turno not in resultado:
            teatro.num_renegados[pelicula] += 1
            return
        if teatro.num_boletos[pelicula] < num_boletos:
            yield env.timeout(0.5)
            return
        teatro.num_boletos[pelicula] -= num_boletos
        if teatro.num_boletos[pelicula] < 2:
            teatro.sold_out[pelicula].succeed()
            teatro.tiempo_agotado[pelicula] = env.now
            teatro.num_boletos[pelicula] = 0
        yield env.timeout(1)


def llegadaClientes(env, teatro):
    while True:
        yield env.timeout(random.expovariate(1/0.5))
        pelicula = random.choice(teatro.peliculas)
        num_boletos = random.randint(1, 6)
        if teatro.num_boletos[pelicula]:
            env.process(ventaBoletos(env, num_boletos, pelicula, teatro))


Teatro = collections.namedtuple(
    'Teatro', 'contador, peliculas, num_boletos, sold_out, tiempo_agotado, num_renegados')

env = simpy.Environment()

contador = simpy.Resource(env, capacity=1)
peliculas = ['Conjuro 3', 'Rapidos y Furiosos 10', 'Pulp Fictions']
num_boletos = {pelicula: NUM_BOLETO for pelicula in peliculas}
sold_out = {pelicula: env.event() for pelicula in peliculas}
tiempo_agotado = {pelicula: None for pelicula in peliculas}
num_renegados = {pelicula: 0 for pelicula in peliculas}

teatro = Teatro(contador, peliculas, num_boletos,
                sold_out, tiempo_agotado, num_renegados)
env.process(llegadaClientes(env, teatro))
env.run(until=TIEMPO_SIMULACION)

root.title("Teatro Carlos Crespi - UPS")
root.geometry("1280x720")

B = tk.Button(root, text ="Generar Reporte", command = generarPDF)
B.pack()

for pelicula in peliculas:
    if teatro.sold_out[pelicula]:
        tiemposAgotados.append(teatro.tiempo_agotado[pelicula])
        lab1 = tk.Label(root,
                        text='Pelicula: %s se agoto en el tiempo %.1f despues de salir a la venta' % (pelicula, teatro.tiempo_agotado[pelicula]))
        lab1.pack()

for pelicula in peliculas:
    if teatro.sold_out[pelicula]:
        numerosRenegados.append(teatro.num_renegados[pelicula])
        lab2 = tk.Label(root,
                        text='Numero de personas que salieron de la fila/renegados %s' % teatro.num_renegados[pelicula])
        lab2.pack()

data1 = {'Peliculas': peliculas,
         'Tiempo_Agotado': tiemposAgotados
        }
df1 = DataFrame(data1,columns=['Peliculas','Tiempo_Agotado'])

data2 = {'Peliculas': peliculas,
         'Numero_Renegados': numerosRenegados
        }
df2 = DataFrame(data2,columns=['Peliculas','Numero_Renegados'])

figure1 = plt.Figure(figsize=(6,5), dpi=110)
ax1 = figure1.add_subplot(111)
bar1 = FigureCanvasTkAgg(figure1, root)
bar1.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH)
df1 = df1[['Peliculas','Tiempo_Agotado']].groupby('Peliculas').sum()
df1.plot(kind='bar', legend=True, ax=ax1, fontsize=10)
ax1.set_title('Peliculas agotadas')
ax1.set_xticklabels(labels=peliculas,rotation = 0)
figure1.savefig('tiempo_agotado.png')

figure2 = plt.Figure(figsize=(6,5), dpi=110)
ax2 = figure2.add_subplot(111)
line2 = FigureCanvasTkAgg(figure2, root)
line2.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH)
df2 = df2[['Peliculas','Numero_Renegados']].groupby('Peliculas').sum()
df2.plot(kind='line', legend=True, ax=ax2, color='r',marker='o', fontsize=10)
ax2.set_title('Personas renegadas')
figure2.savefig('personas_renegadas.png')

root.mainloop()