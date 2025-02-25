# -*- coding: utf-8 -*-
"""
numericsprocessor

@author: MrMai
"""

import numpy as np
from scipy.special import kn

import scipy.constants as const
# import sympy as sp
# from scipy.special import jv 
# from datetime import datetime
# starttime = datetime.now()

## My >>toolboxes<<
# import spectrum
# import green
# import psi_perp
import wave_functions
from tools import read_matlab_data, read_data_metadata
from functions import permitivity_drude

import matplotlib.pyplot as plt
import matplotlib.colors as colors
inchtocm = 2.54
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ['Computer Modern Roman'],
    #"figure.figsize" : [8/inchtocm, 8/inchtocm]
    })
# %matplotlib auto       # interactive plots
# %matplotlib inline     # non-interactive plots


#%% read data

eigencharges = read_matlab_data("Data/eigencharges")
eigenpseudolambdas = np.diag(np.loadtxt("Data/eigenpseudolambdas.csv", delimiter=","))
pfacepos = read_matlab_data("Data/pfacepos")
pfacearea = read_matlab_data("Data/pfacearea")

numofpoints, numofstates  = np.shape(eigencharges)

#%% Arrays
xm = 40e-9
ym = xm

print("Preparing input arrays ... ", end="")
numofxpoints = 70
numofypoints = 70
xrange = [-xm,xm]
yrange = [-ym,ym]
dx = (xrange[1] - xrange[0])/(numofxpoints-1)
dy = (yrange[1] - yrange[0])/(numofypoints-1)

xx = np.linspace(xrange[0], xrange[1], numofxpoints)
yy = np.linspace(yrange[0], yrange[1], numofypoints)

X, Y   = np.meshgrid(xx, yy, indexing="ij")
print("DONE")
#%% parameters
print("Preparing parameters ... ", end="")
qz = np.sqrt(2 * const.m_e * 60e3 * const.eV) / const.h
v = 0.446 * const.c



print("DONE")

#%% particle
XX = np.array([X] * numofpoints)
YY = np.array([Y] * numofpoints)
sx = np.moveaxis(np.array([[pfacepos[:,0]]]), 2, 0).astype(float) * 1e-9
sy = np.moveaxis(np.array([[pfacepos[:,1]]]), 2, 0).astype(float) * 1e-9
sz =  pfacepos[:,2] * 1e-9


#%%% plot the particle
fig = plt.figure()
ax = fig.add_subplot(projection='3d')
ax.scatter(sx,sy,sz)


#%% Omegas and alphas
omegas =  np.linspace(.6,1,50) *1e16 #np.linspace(3,9,50) * const.eV/const.hbar
omega_p = 9.1 * const.eV/const.hbar
gamma_p = 0.15 * const.eV/const.hbar
epsilonko = permitivity_drude(omegas, omega_p, gamma_p)


#%% O M E G A S   A   G F A C T O R S
# omegas chosen to fit the maxima of absorption peaks
omegas = np.array([4.2,  4.5]) * 1e15 # np.linspace(.3,0.55,151) *1e16
epsilons = permitivity_drude(omegas, omega_p, gamma_p)
eigenlambdas = eigenpseudolambdas / 2 / np.pi
gfactorss = np.imag(-2 / (np.array([epsilons]).T @ np.array([(1 + eigenlambdas)]) + (1 - eigenlambdas) ) )

#%% firstmodes restriction
nmax = 2
preskoc=2
gfactors = gfactorss[:,preskoc:preskoc+nmax].T
# #%%
# labels = (np.array(["$n = "]*(nmax), dtype=np.object) 
#           + (np.array(range(nmax+1)[1:])).astype(str).astype(np.object) 
#           + np.array([" $"]*(nmax), dtype=np.object)
#           )
# fig, ax = plt.subplots()
# ax.plot(omegas, gfactors.T, label = labels)
# ax.legend(loc = "center left")
# ax.grid()
# ax.set_xlim(omegas[0], omegas[-1])
# ax.set(xlabel = "$\omega \, / \, \mathrm{rad\cdot s^{-1}}$",
#        ylabel = "Im$[-g_n(\omega)]$")

# fig.savefig("gfactors.png", dpi=150)

#%% P O T E N T I A L S

potentials = [] 
for n in range(numofstates)[preskoc:preskoc+nmax]:
    potential = []
    for omega in omegas:
        potentialek = (
                    2 * pfacearea * eigencharges[:,n] * np.exp(-1j * omega / v * sz) @
                    np.moveaxis(kn(0, omega / v * np.sqrt((XX-sx)**2 + (YY-sy)**2) ), 0, 1)
                    )
        potential.append(potentialek)
    potentials.append(potential)
    print(f"potential number {n-preskoc+1}: DONE")
potentials = np.array(potentials)

#%%
np.save("Data/potentials.npy", potentials)
#%% W A V E F U N C T I O N S

xc = 0e-9
yc = 0e-9

qc = qz * 3e-3     # cutoff q for queen (detector)
qa = qz * 3e-3      # cutoff q for initial psi (aperture)

lf=1
li=1

meshx = 64
meshy = 64
xbound = 3e-8
ybound = 3e-8

xcs = np.linspace(-xbound,xbound, meshx) 
ycs = np.linspace(-ybound,ybound, meshy) 

Xcs, Ycs = np.meshgrid(xcs,ycs)

XX = np.moveaxis(np.array([[X]]),(0,1),(2,3))
YY = np.moveaxis(np.array([[Y]]),(0,1),(2,3))
Xcs = np.array([[Xcs]])
Ycs = np.array([[Ycs]])
#%%
print("Preparing the initial psis ... ", end="")
psii = np.array([[wave_functions.psiperp(li, XX-Xcs,YY-Ycs,qa)]])
psif = np.array([[wave_functions.psiperp(li, XX-Xcs,YY-Ycs,qc)]])
print("DONE")

# #%% plot of the wavefunction
# fig, (axabs, axphase) = plt.subplots(1,2,sharey=True)
# fig.set_size_inches(18/inchtocm, 10/inchtocm)

# axabs.set_title("$\mathrm{Abs}\,( \psi )$")
# ax1 = axabs.pcolormesh(X*1e9,Y*1e9,np.abs(psii[0,0,:,:]), cmap="viridis")
# axabs.set_aspect(1)
# plt.colorbar(ax1, ax=axabs, fraction=0.046, pad=0.035)
# axabs.set(xlabel = "$x \, / \, \mathrm{nm}$",
#        ylabel = "$y \, / \, \mathrm{nm}$")

# axphase.set_title("$\mathrm{Arg}\,( \psi )$")
# ax2 = axphase.pcolormesh(X*1e9,Y*1e9,np.angle(psii[0,0,:,:]), cmap="hsv")
# axphase.set_aspect(1)
# plt.colorbar(ax2, ax=axphase, fraction=0.046, pad=0.035)
# axphase.set(xlabel = "$x \, / \, \mathrm{nm}$",)


# fig.savefig("Psi.png", dpi=150)

#%% S P E C T R U M
integrandek = psii * psif  * np.moveaxis(np.array([[potentials]]), (0,1),(4,5))
# plt.imshow(np.abs(integrandek[0,1,:,:]))
integralek = np.sum( integrandek, axis = (2,3) ) * dx * dy
gammas = np.sum(  np.reshape(gfactors,(2,2,1,1)) * np.abs(integralek)**2   , axis=0)

#spectrum = np.array([omegas,gammas]).T
#%% S A V E

bonding = gammas[0,:,:]
antibonding = gammas[1,:,:]

metadata = {'li': li,
            'lf': lf,
            'meshx': meshx,
            'meshy': meshy,
            'xbound': xbound,
            'ybound': ybound,
            'qz': qz,
            'qa': qa,
            'qc':qc,
            'v': v,
            }

metadata['bondingantibonding'] = 0
metadata['omega'] = omegas[metadata['bondingantibonding']]
np.savetxt(f"Maps/map_bonding_li{li}_lf{lf}_{meshx}x{meshy}.csv", bonding, header=str(metadata))

metadata['bondingantibonding'] = 1
metadata['omega'] = omegas[metadata['bondingantibonding']]
np.savetxt(f"Maps/map_antibonding_li{li}_lf{lf}_{meshx}x{meshy}.csv", antibonding, header=str(metadata))



#%% DICHROISM
dataB1, metadataB1 = read_data_metadata('Maps/map_bonding_li1_lf1_64x64.csv')
dataAB1, metadataAB1 = read_data_metadata('Maps/map_antibonding_li1_lf1_64x64.csv')
dataB2, metadataB2 = read_data_metadata('Maps/map_bonding_li-1_lf-1_64x64.csv')
dataAB2, metadataAB2 = read_data_metadata('Maps/map_antibonding_li-1_lf-1_64x64.csv')

dichbond     = (dataB1 - dataB2) / (dataB2 + dataB1)
dichantibond = (dataAB1 - dataAB2) / (dataAB2 + dataAB1)

#%%
# plt.imshow(bonding)
plt.imshow(antibonding)
# plt.imshow(dichbond)
# plt.imshow(dichantibond)

#%% PLOT
meshx = metadataB1['meshx']
meshy = metadataB1['meshy']
xbound = metadataB1['xbound']
ybound = metadataB1['ybound']

xcs = np.linspace(-xbound,xbound, meshx) 
ycs = np.linspace(-ybound,ybound, meshy) 

Xcs, Ycs = np.meshgrid(xcs,ycs)

#%%% plot dichbond

fig,ax = plt.subplots()

im = ax.pcolormesh(Xcs,Ycs,dichbond, 
              cmap = "seismic",
              vmin = -1,
              vmax = 1,
              )
ax.set_aspect(1)

cax = fig.add_axes([0.8, 0.1, 0.02, 0.8])
fig.colorbar(im, cax=cax, orientation='vertical')
plt.show()


#%%% plot dichantibond

fig,ax = plt.subplots()

im = ax.pcolormesh(Xcs,Ycs,dichantibond, 
              cmap = "seismic",
              vmin = -1,
              vmax = 1,
              )
ax.set_aspect(1)

cax = fig.add_axes([0.8, 0.1, 0.02, 0.8])
fig.colorbar(im, cax=cax, orientation='vertical')
plt.show()

#%%% plot log dichantibond

fig,ax = plt.subplots()

im = ax.pcolormesh(Xcs,Ycs,np.log10(np.abs(dichantibond)), 
              cmap = "gray",
              vmin = -1,
              vmax = 0,
              )
ax.set_aspect(1)

cax = fig.add_axes([0.8, 0.1, 0.02, 0.8])
fig.colorbar(im, cax=cax, orientation='vertical')
plt.show()


#%%% plot bonding

fig,ax = plt.subplots()

im = ax.pcolormesh(Xcs,Ycs, bonding, 
              cmap = "gray",
              # vmin = -3,
              # vmax = 0,
              )
ax.set_aspect(1)

cax = fig.add_axes([0.8, 0.1, 0.02, 0.8])
fig.colorbar(im, cax=cax, orientation='vertical')
plt.show()

#%%% plot antibonding

fig,ax = plt.subplots()

im = ax.pcolormesh(Xcs,Ycs, antibonding, 
              cmap = "gray",
              # vmin = -3,
              # vmax = 0,
              )
ax.set_aspect(1)

cax = fig.add_axes([0.8, 0.1, 0.02, 0.8])
fig.colorbar(im, cax=cax, orientation='vertical')
plt.show()



#%%
fig,ax = plt.subplots()
figdich,axdich = plt.subplots()
#linestyles = ["-", (0,(5,1)), (0,(3,1)), (0,(3,1,1,1)), (0,(3,1,1,1,1,1)), (0,(3,1,1,1,1,1,1))]
xcs = ["-2e-08", "-1e-08", "0.0", "1e-08", "2e-08", "2.5e-08", "3e-08"]
markers = np.array(["$"]*7,dtype=object)+np.array(range(7)).astype(str).astype(object)+np.array(["$"]*7,dtype=object)

for i in range(7):
    xc = xcs[i]
    fname1 = f"Data/fullspectrum_li1_lf1_xc{xc}_yc{xc}.csv"
    data1, metadata1 = read_matlab_data(fname1)
    omegas1 = data1[:,0]
    gammas1 = data1[:,1]
    
    fname2 = f"Data/fullspectrum_li-1_lf-1_xc{xc}_yc{xc}.csv"
    data2, metadata2 = read_matlab_data(fname2)
    omegas2 = data2[:,0]
    gammas2 = data2[:,1]
    
    ax.plot(omegas1, gammas1, 
            color="red", 
            label=f"$x_c = y_c = {round(float(xc)*1e9)}$ nm",
            marker=markers[i],
            markevery=5,
            mec=(0,0,0))
    ax.plot(omegas2, gammas2, color="blue", 
            label=f"$x_c = y_c = {round(float(xc)*1e9)}$ nm",
            marker=markers[i],
            markevery=5,
            mec=(0,0,0))
    
    dichroism = (gammas1-gammas2)/(gammas1+gammas2)
    axdich.plot(omegas1, dichroism, 
                label=f"$x_c = y_c = {round(float(xc)*1e9)}$ nm")
        
ax.legend()
axdich.legend()
axdich.grid()
axdich.set_xlim(omegas1[0],omegas1[-1])





#%%
fig,ax = plt.subplots()
figdich,axdich = plt.subplots()
#linestyles = ["-", (0,(5,1)), (0,(3,1)), (0,(3,1,1,1)), (0,(3,1,1,1,1,1)), (0,(3,1,1,1,1,1,1))]
xcs = ["-2e-08", "-1e-08", "0.0", "1e-08", "2e-08", "2.5e-08", "3e-08"]
markers = np.array(["$"]*7,dtype=object)+np.array(range(7)).astype(str).astype(object)+np.array(["$"]*7,dtype=object)

for i in range(7):
    xc = xcs[i]
    fname1 = f"Data/fullspectrum_li1_lf1_xc{xc}_yc{xc}.csv"
    data1, metadata1 = read_matlab_data(fname1)
    omegas1 = data1[:,0]
    gammas1 = data1[:,1]
    
    fname2 = f"Data/fullspectrum_li-1_lf-1_xc{xc}_yc{xc}.csv"
    data2, metadata2 = read_matlab_data(fname2)
    omegas2 = data2[:,0]
    gammas2 = data2[:,1]
    
    ax.plot(omegas1, gammas1, 
            color="red", 
            label=f"$x_c = y_c = {round(float(xc)*1e9)}$ nm",
            marker=markers[i],
            markevery=5,
            mec=(0,0,0))
    ax.plot(omegas2, gammas2, color="blue", 
            label=f"$x_c = y_c = {round(float(xc)*1e9)}$ nm",
            marker=markers[i],
            markevery=5,
            mec=(0,0,0))
    
    dichroism = (gammas1-gammas2)/(gammas1+gammas2)
    axdich.plot(omegas1, dichroism, 
                label=f"$x_c = y_c = {round(float(xc)*1e9)}$ nm")
        
ax.legend()
axdich.legend()
axdich.grid()
axdich.set_xlim(omegas1[0],omegas1[-1])


#%%
xcs = ["-2e-08", "-1e-08", "0.0", "1e-08", "2e-08", "2.5e-08", "3e-08"]
markers = np.array(["$"]*7,dtype=object)+np.array(range(7)).astype(str).astype(object)+np.array(["$"]*7,dtype=object)
for i in range(7):
    xc = xcs[i]
    fname1 = f"Data/fullspectrum_li1_lf1_xc{xc}_yc{xc}.csv"
    data1, metadata1 = read_matlab_data(fname1)
    omegas1 = data1[:,0]
    gammas1 = data1[:,1]
    
    fname2 = f"Data/fullspectrum_li-1_lf-1_xc{xc}_yc{xc}.csv"
    data2, metadata2 = read_matlab_data(fname2)
    omegas2 = data2[:,0]
    gammas2 = data2[:,1]
    xlims = (omegas1[0],omegas1[-1])
    
    fig, (ax1) = plt.subplots(1,1)
    ax2 = ax1.twinx()
    
    ax1.plot(omegas1, gammas1, 
            color="red", 
            label="$l = +1$",
            #marker=markers[i],
            #markevery=5,
            #mec=(0,0,0)
            )
    ax1.plot(omegas2, gammas2, 
            color="blue", 
            label="$l = -1$",
            #marker=markers[i],
            #markevery=5,
            #mec=(0,0,0)
            )
    
    dichroism = (gammas1-gammas2)/(gammas1+gammas2) 
    ax2.plot(omegas1, dichroism, 
             color="k",
             #label=f"$x_c = y_c = {round(float(xc)*1e9)}$ nm"
             )
    
    ax1.grid()
    ax1.legend(loc="upper left")
    #ax2.legend(loc = "upper right")
    
    ax1.set_ylabel("$\Gamma(\omega)$ / arb. u.", color="purple")
    ax2.set_ylabel("$D(\omega)$", color="k")
    ax1.set_xlabel("$\omega \ / \mathrm{rad \cdot s^{-1}}$")
    ax1.tick_params(axis='y', labelcolor="purple")
    ax1.spines['left'].set_color('purple')
    ax2.tick_params(axis='y', labelcolor="k")
    ax2.spines['left'].set_color('purple')
    ax1.set_xlim(xlims)
    
    
    ax1.set_title(f"$x_c = y_c = {round(float(xc)*1e9)}$ nm")
    fig.set_figwidth(17/inchtocm)
    fig.show()
    fig.savefig(f"Spectra/EELSF_xc{xc}_w.png",
                dpi = 150, 
                bbox_inches='tight', 
                #transparent=True
                )