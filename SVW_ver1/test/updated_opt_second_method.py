# Initiated by Zihang Wang, 


# %% Importing
#########################################################
#########################################################

import os
import sys

# get path of this script
#path_this_script = os.getcwd()
path_this_script = os.path.realpath(__file__)

# add the ./src/ path to the search path
path_this_script_splitted = os.path.split(path_this_script)
path_this_script_splitted = os.path.split(path_this_script_splitted[0])
path_to_src = os.path.join(path_this_script_splitted[0], 'src')
sys.path.append(path_to_src)  # I could have used sys.path.append('../src/'), but it didn't work with the debugger

from SphTools import *
from scipy.optimize import minimize
from scipy.optimize import least_squares,lsq_linear


# %% Input
#########################################################
#########################################################

# define the maximum order for expansion
L_max = 50

# define frequency, relative permittivity and permeability
Eps_r=1; Mu_r=1

Mu_vacuum = 1.25663706212e-6    # vacuum magnetic permeability
Eps_vacuum = 8.8541878128e-12   # vacuum electric permittivity
ZVAC = 376.73031346177          # impedance of free space
c = 299792458                   # the speed of light, m/s
pi = np.pi

Omega = 3e14
Eps=Eps_vacuum
Mu = Mu_vacuum
lMax = 3
k=Omega/c

span = 2*1/k; n_point_per_side = span*10
x_min, x_max = span,-span
y_min, y_max = span, -span
z_min, z_max = span, -span


# derrived values
Mu =   Mu_vacuum       # magnetic permeability of surrounding media
Eps =Eps_vacuum    # electric permittivity of surrounding media
Z_imped = ZVAC*np.sqrt(Mu/Eps)

#%% Plane wave
def plane_wave(x,y,z,polar_psi,polar_chi,a,b,E0,k):
    ''' 
    Calculate electric and magnetic fields for a general plane wave.

    Parameters
    ==========
    polar_psi: rotation from basis e_a
    polar_chi: tangent of ratio between semi-major and semi-minor tan(polar_chi)=(major/minor) 
    a: angle around z-axis
    b: angle from z-axis
    k: wave number 

    Return
    ======
    E,H

    Authord: Zihang Wang (Steve).
    '''
    e=1
    mu=1
    x=x.reshape((totaL_len,))
    y=y.reshape((totaL_len,))
    z=x.reshape((totaL_len,))

    loc_array=np.array([x,y,z]).transpose()
    #print(loc_array)
    E_a=E0*(np.cos(polar_chi)*np.sin(polar_psi)-1j*np.sin(polar_chi)*np.cos(polar_psi))
    E_b=E0*(np.cos(polar_chi)*np.cos(polar_psi)+1j*np.sin(polar_chi)*np.sin(polar_psi))
    e_a=np.array([-np.sin(a),np.cos(a),0])
    e_b=np.array([np.cos(a)*np.cos(b),np.sin(a)*np.cos(b),-np.sin(b)])
    e_k=np.array([np.cos(a)*np.sin(b),np.sin(a)*np.sin(b),np.cos(b)])
    
    #Projection wave-vector 
    e_a=np.tile(e_a,(len(x),1))
    e_b=np.tile(e_b,(len(x),1))
    e_k=np.tile(e_k,(len(x),1))
    
    k_vec=k*e_k
    Dot_product=np.sum(k_vec*loc_array,axis=1)
    
    Dot_product=np.tile(Dot_product,(3,1)).transpose()
    E=(E_a*e_a+E_b*e_b)*np.exp(1j*Dot_product)
    
    # Magnetic field, 
    H=np.sqrt(e/mu)*np.cross(e_k,E)
    
    return E,H
    
# %% Calculations
#########################################################
#########################################################

# define the cooridnates of points
x=np.linspace(x_min,x_max ,10)
y=np.linspace(y_min,y_max,10)
z=np.linspace(z_min,z_max,10)

totaL_len=len(x)*len(y)*len(z)
x,y,z=np.meshgrid(x,y,z)

r,theta,phi = convert_coordinates_Cart2Sph(x, y, z)

# define plane wave parameters 
polar_psi=0
polar_chi=0
a=np.pi/3
b=np.pi/5
E0=1
k=Omega/c#2*pi/span 

E_plane_wave=plane_wave(x,y,z,polar_psi,polar_chi,a,b,E0,k)[0]
E_plane_wave=np.reshape(E_plane_wave, (3*totaL_len,1 ), order='F')

Recon_E=np.reshape(E_plane_wave, (totaL_len,3 ), order='F')

Rec_E_mag=np.reshape(np.abs(E_plane_wave), (totaL_len,3 ), order='F')
# %% Testing by using pure M wave 

MN_test=1.2*get_M_N_waves(r,theta,phi, -1,1, Omega, Eps, Mu, kind=1, return_Cartesian=True)[0]
Col_1=MN_test[:,:,:,0]
Col_2=MN_test[:,:,:,1]
Col_3=MN_test[:,:,:,2]

# reshape for x 
Col_1=np.reshape(Col_1,(totaL_len,))
Col_2=np.reshape(Col_2,(totaL_len,))
Col_3=np.reshape(Col_3,(totaL_len,))

# point matrix 
E_test=np.vstack([Col_1,Col_2,Col_3])

E_test=np.reshape(E_test, (3*totaL_len,1 ), order='F')

alpha_test = get_alpha_for_LMP(1, -1, 0)
print(E_test.shape)
print(alpha_test)

# %% creating WV matrix
N_max=3

Alpha_list=np.array([])
# n loop 
#for i in range(0,len(Nested_array)):

alpha_max=get_N_SphericalWaves_given_L_max(N_max)
print(alpha_max)
Row_vec=np.zeros(  (3*totaL_len, alpha_max)  )*1j  # I have just made 'alpha_max' to be at the column


# setting a list of frequency

Omega_span=0.002*Omega
Omega_expand_gap=20
omega_left=Omega-Omega_span
omega_right=2*Omega#+Omega_span

Omega_expand=np.linspace(omega_left,omega_right,Omega_expand_gap)

E_cal_cum=0

Coff_matrix=np.zeros((totaL_len*3,alpha_max))
for o in range(0,Omega_expand_gap):
    Omega_current=Omega_expand[o]

    for n in range(1,N_max+1):
        
        for m in range(-n,n+1):
            #print(m)
            MN=get_M_N_waves(r,theta,phi, m,n, Omega_current, Eps, Mu, kind=1, return_Cartesian=True)
            ############ I think this should be two outputs here
            for p in [0,1]:
                #print(p)
                alpha = get_alpha_for_LMP(n, m, p)
                Alpha_list=np.append(Alpha_list,alpha)
                MN_c=MN[p]
                Col_1=MN_c[:,:,:,0]
                Col_2=MN_c[:,:,:,1]
                Col_3=MN_c[:,:,:,2]

                Col_1=np.reshape(Col_1,(totaL_len,))
                Col_2=np.reshape(Col_2,(totaL_len,))
                Col_3=np.reshape(Col_3,(totaL_len,))

                # point matrix 
                E_p=np.vstack([Col_1,Col_2,Col_3])

                E_p=np.reshape(E_p, (len(Col_1)+len(Col_2)+len(Col_3), ), order='F')
    # I think you intended Col_3
                #print(Vec_fuc_W)
                # Wavefunction 
                Row_vec[:,alpha]=E_p # I just replaced 'alpha' index, to make it representative for columns ---- Row_vec[alpha,:]=Vec_fuc_W
            
            

    # Real fit 
    Row_vec_real_real_part=Row_vec.real
    Row_vec_imag_real_part=Row_vec.imag

    Total_real_part=np.vstack((Row_vec_real_real_part,Row_vec_imag_real_part))
    if o==0:
        Coff_matrix=Total_real_part
    else:
        Coff_matrix=np.hstack([Coff_matrix,Total_real_part])
        # array of c 

E_basis_real=E_plane_wave.real
# array of d
E_basis_imag=E_plane_wave.imag

E_basis_total_real_part=np.vstack((E_basis_real,E_basis_imag))

from scipy.optimize import nnls
Fit=nnls(Coff_matrix, E_basis_total_real_part[:,0])
#Fit = np.linalg.lstsq(Coff_matrix, E_basis_total_real_part) 
Err=Fit[1]
C=np.array([Fit[0]]).T       #print(alpha)

E_cal=np.matmul(Coff_matrix, C) # I removed the transpose because I changed the 'alpha' index to be a column index
leng_cal=len(E_cal)
E_cal_real=E_cal[:,0][0:int(leng_cal/2)]
E_cal_imag=E_cal[:,0][int(leng_cal/2):]*1j
E_calculate=E_cal_real+E_cal_imag


#Recon_E_cal=np.reshape(E_cal_cum, (totaL_len,3 ), order='F')

#%% plot E
#f,axs=plt.subplots(2,1)
#axs[0].pcolormesh(X, Y, Z, cmap = cm.gray) 

#%% Linear 
f,axs=plt.subplots(2,3)
place_hod=np.linspace(0,1,int(leng_cal/2))
#plt.plot(place_hod,E_cal)
#plt.plot(place_hod,E_basis_total_real_part)
ax_1=axs[0,0]
ax_2=axs[0,1]
ax_3=axs[1,0]
ax_4=axs[1,1]
ax_5=axs[1,2]
ax_6=axs[0,2]

ax_1.plot(place_hod,E_calculate.imag)
ax_2.plot(place_hod,E_plane_wave.imag)
ax_5.plot(place_hod,E_calculate.imag-E_plane_wave[:,0].imag)

ax_3.plot(place_hod,E_calculate.real)
ax_4.plot(place_hod,E_plane_wave.real)
ax_6.plot(place_hod,E_calculate.real-E_plane_wave[:,0].real)
#%%

s=np.linspace(0,1,len(C))
plt.plot(s,C)
# %% Minimize testing 
#print(E_desire)
import time
import warnings
import numpy as np
from scipy.optimize import minimize, rosen

class TookTooLong(Warning):
    pass

class MinimizeStopper(object):
    def __init__(self, max_sec=0.1):
        self.max_sec = max_sec
        self.start   = time.time()

    def __call__(self, xk):
        # callback to terminate if max_sec exceeded
        elapsed = time.time() - self.start
        if elapsed > self.max_sec:
            warnings.warn("Terminating optimization: time limit reached",
                          TookTooLong)
        else:
            # you might want to report other stuff here
            print("Elapsed: %.3f sec" % elapsed)
# init stopper
minimize_stopper = MinimizeStopper()


def cost_fuc(x):
    leng_x=len(x)
    #new_x=np.reshape(x,(int(leng_x/2),2))
   # real_x=x[0:int(leng_x)]
   # img_x=new_x[:,1]*1j
   # reco_x=new_x[:,0]+img_x
    E_cal_complex=np.matmul(Coff_matrix, x) 
    
     
    Cost_precent=2*(E_cal_complex-E_basis_total_real_part.T[0,:])/(E_cal_complex-E_basis_total_real_part.T[0,:])
    print(np.sum(np.absolute(Cost_precent)))

    return np.sum(np.absolute(Cost_precent))

#np.ones(Row_vec.shape[1])*10**(-5)
#%%
initial_guess=np.ones(Coff_matrix.shape[1])
print('-----')
# minimze
res = minimize(cost_fuc,
               x0       = initial_guess,
               method   ="COBYLA",
               options  = { "disp":True},
               callback = minimize_stopper.__call__)

E_cal_complex=np.matmul(Coff_matrix, res.x)
leng_cal=len(E_cal_complex)
E_cal_comp_real=E_cal_complex[0:int(leng_cal/2)]
E_cal_comp_imag=E_cal_complex[int(leng_cal/2):]*1j
E_calculate_comp=E_cal_comp_real+E_cal_comp_imag


#%% Minimizer
f,axs=plt.subplots(2,3)
place_hod=np.linspace(0,1,int(leng_cal/2))
#plt.plot(place_hod,E_cal)
#plt.plot(place_hod,E_basis_total_real_part)
ax_1=axs[0,0]
ax_2=axs[0,1]
ax_3=axs[1,0]
ax_4=axs[1,1]
ax_5=axs[1,2]
ax_6=axs[0,2]

ax_1.plot(place_hod,E_calculate_comp.imag)
ax_2.plot(place_hod,E_plane_wave.imag)
ax_5.plot(place_hod,E_calculate_comp.imag-E_plane_wave[:,0].imag)

ax_3.plot(place_hod,E_calculate_comp.real)
ax_4.plot(place_hod,E_plane_wave.real)
ax_6.plot(place_hod,E_calculate_comp.real-E_plane_wave[:,0].real)

#%% Pytorch
'''
import torch
import torch.nn.functional as F
# array of c 
E_basis_real=E_basis.real
# array of d
E_basis_imag=E_basis.imag

E_basis_total_real_part= np.vstack((E_basis_real,E_basis_imag))


Row_vec_real_real_part=Row_vec.real
Row_vec_imag_real_part=Row_vec.imag

Total_real_part=np.vstack((Row_vec_real_real_part,Row_vec_imag_real_part))



y=torch.from_numpy(E_basis_total_real_part)


class Net(torch.nn.Module):
    def __init__(self,n_feature,n_hidden,n_output):
        super(Net,self).__init__()

        self.hidden=torch.nn.Linear(n_feature,n_hidden)
        self.predict=torch.nn.Linear(n_hidden,n_output)

    def forward(self,x):
        x=F.relu(self.hidden(x))
        x=self.predict(x)
        return x 

net=Net(126,1,1)
print(net)

def cost_fuc(x_predicted,y):
    leng_x=len(x_predicted)
    x_predicted=x_predicted.numpy()
    y=y.numpy()
    y_predicted=np.matmul(Total_real_part,x_predicted).T 
    print(y_predicted.shape)
    print(y[:,0].shape)
    Cost_precent=2*(y_predicted-y[:,0])/(y_predicted+y[:,0])
    
    return torch.from_numpy(np.absolute(Cost_precent))


x_p=torch.linspace(0,1,Total_real_part.shape[1])
optimizer=torch.optim.SGD(net.parameters(),lr=0.2)
ls=cost_fuc(x_p,y)
pred_fuc=net(x_p)
optimizer.zero_grad()
ls.backward()
#optimizer.step()

'''












# %% using np.linalg.lstsq ------------------------------------------------
#Cost function 
from scipy.optimize import minimize


#_test=get_M_N_waves(r,theta,phi, 0,1, Omega, Eps, Mu, kind=1, return_Cartesian=True)[0]
#E_basis=np.reshape(E_test, (len(x)+len(y)+len(z),1), order='F')

# array of c 
E_basis_real=E_basis.real
# array of d
E_basis_imag=E_basis.imag

E_basis_total_real_part=np.vstack((E_basis_real,E_basis_imag))

# Real fit 
Row_vec_real_real_part=Row_vec.real
Row_vec_imag_real_part=Row_vec.imag

Total_real_part=np.vstack((Row_vec_real_real_part,Row_vec_imag_real_part))


#one_array=np.ones((len(E_basis_total_real_part),1))
#Total_real_part=np.hstack([Total_real_part,one_array])




#initial_guess=np.hstack([1,initial_guess])

E_cal_complex=np.matmul(Total_real_part, initial_guess) 
Cost_precent=2*(E_cal_complex-E_basis_total_real_part.T[0,:])/(E_cal_complex+E_basis_total_real_part.T[0,:])

res = minimize(cost_fuc, initial_guess, method='nelder-mead',
               options={'xatol': 1e-8, 'disp': True})




k=0
while k<10:
    
    c=cost_fuc(initial_guess)
    initial_guess=np.random.rand(Row_vec.shape[1])
    k+=1
    print(c)



#+np.random.rand(Row_vec.shape[1])*1j

















# %% using np.linalg.lstsq





# electric field 


#para=60
#Total_real_part=Total_real_part[np.ix_(range(0,para),range(0,len(E_basis_total_real_part)))]

#Total_real_part=Total_real_part[np.ix_(range(0,para),range(0,para))]

#Comp=np.linalg.solve(Total_real_part,E_basis_total_real_part)
#E=np.matmul(Total_real_part, Comp) 

Fit = np.linalg.lstsq(Total_real_part, E_basis_total_real_part) 
Err=Fit[1]
C=Fit[0]

#E_cal=np.matmul(Row_vec.transpose(), C)
E_cal=np.matmul(Total_real_part, C) # I removed the transpose because I changed the 'alpha' index to be a column index

# Recombied 
E_cal_complex=np.reshape(E_cal,(int(len(E_cal)/2),2))


# Precent Difference 
Err=2*(E_cal_complex-E_basis)/(E_cal_complex+E_basis)

E_summ=np.hstack((E_cal,E_basis_total_real_part))

print(E_summ)

# %% using scipy.optimize.least_squares 
#def get_fields_from_C(x, Row_vec):
import pandas as pd
pand=pd. DataFrame(E_summ)


# %%

def cost_fuc(z):
    E_cal_complex=np.matmul(Total_real_part, z) 
    Cost_precent=2*(E_cal_complex-E_basis_total_real_part.T[0,:])/(E_cal_complex+E_basis_total_real_part.T[0,:])

    return np.sum(np.absolute(Cost_precent))
def f_wrap(x):
    fx = cost_fuc(x[0] + 1j*x[1])
    return np.array([fx.real, fx.imag])

initial_guess_x=np.random.rand(Row_vec.shape[1])
initial_guess_y=np.random.rand(Row_vec.shape[1])
res_wrapped = least_squares(f_wrap, (initial_guess_x,initial_guess_y))

z = res_wrapped.x[0] + res_wrapped.x[1]*1j

# %%

 cost_fuc(initial_guess_x + 1j*initial_guess_y)

# %%
