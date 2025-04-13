#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 12 19:56:37 2023

@author: vamsi
Modified: Friday, April 11, 2025 - Added CSV output functionality
"""

import numpy as np
import matplotlib.pyplot as plt
import math
from mpl_toolkits.mplot3d import Axes3D
import random
from matplotlib.colors import LogNorm, Normalize
import pandas as pd
import numpy as np
import sys
import os

# Create results_sigcomm directory if it doesn't exist
if not os.path.exists("results_sigcomm"):
    os.makedirs("results_sigcomm")

#
dump="dump_sigcomm/"
# dump="dumps/1-baseline/"
plots="plots_sigcomm/"
# plots="/home/vamsi/plots_sigcomm/"

LOSSLESS=0
LOSSY=1

DT=101
FAB=102
ABM=110
REVERIE=111

DCQCNCC=1
INTCC=3
TIMELYCC=7
PINTCC=10
CUBIC=2
DCTCP=4

# DUMP_DIR/evaluation-$alg-$RDMACC-$TCPCC-$rdmaload-$tcpload-$rdmaburst-$tcpburst-$egresslossyFrac-$gamma.fct

colors={}
colors[str(DT)]='red'
colors[str(ABM)]='blue'
colors[str(REVERIE)]='green'

markers={}
markers[str(DT)]='x'
markers[str(ABM)]='^'
markers[str(REVERIE)]='P'

names={}
names[str(DT)]="DT"
names[str(ABM)]="ABM"
names[str(REVERIE)]="Reverie"

algs=[str(DT),str(ABM),str(REVERIE)]
loads=["0.2","0.4","0.6","0.8"]
loadsint=[0.2,0.4,0.6,0.8]

# bursts=["500000", "1000000"]
bursts=["500000", "1000000","1500000", "2000000", "2500000"]

buffer=2610000

plt.rcParams.update({'font.size': 18})

# Function to write experiment results_sigcomm to CSV
def write_experiment_results_sigcomm_to_csv(title, headers, data, filename):
    """Write experiment results_sigcomm to a CSV file in the results_sigcomm directory"""
    filepath = os.path.join("results_sigcomm", filename)
    
    # Convert data to a pandas DataFrame for easy CSV writing
    df = pd.DataFrame(data, columns=headers)
    
    # Write to CSV file without rounding
    df.to_csv(filepath, index=False, float_format='%g')
    
    print(f"results_sigcomm written to {filepath}")

# EXPERIMENT 1: TCP Load Impact
# =============================

loads=["0.2","0.4","0.6","0.8"]
loadsint=[0.2,0.4,0.6,0.8]
bursts=["500000", "1000000","1500000", "2000000", "2500000"]

rdmacc=str(DCQCNCC)
tcpcc=str(DCTCP)
rdmaburst="2000000"
tcpburst="0"
egresslossyFrac="0.8"
gamma="0.999"
rdmaload="0"

# Confirmed column names from C++ source:
# - FCT file: timestamp, flowsize, fctus, basefctus, slowdown, baserttus, priority, incastflow
# - TOR file: switch, totalused, egressOccupancyLossless, egressOccupancyLossy, ingressPoolOccupancy, headroomOccupancy, sharedPoolOccupancy, time
# - PFC file: Time, NodeId, NodeType, IfIndex, type

# Prepare headers and data for TCP load experiment
tcp_load_headers = ["TCP Load", "Algorithm", "Short FCT 95%", "PFC Pauses", "TCP Short FCT 99%", "Lossless Buffer (%)", "Lossy Buffer (%)"]
tcp_load_data = []

for tcpload in loads:
    shortfct95=list()
    shortfct99=list()
    shortfct999=list()
    shortfctavg=list()
    tcpshortfct99=list()
    numpfc=list()
    lossy=list()
    lossless=list()
    total=list()
    longfctav=list()
    medfctav=list()
    for alg in algs:
        fctfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.fct'
        torfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.tor'
        outfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.out'
        pfcfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.pfc'
        
        fctDF = pd.read_csv(fctfile,delimiter=' ')
        shortfctDF = fctDF[(fctDF["incastflow"]==1)&(fctDF["priority"]==3)]
        
        tcpshortfctDF = fctDF[(fctDF["flowsize"]<100000)&(fctDF["priority"]==1)]
        shortfct = list(tcpshortfctDF["slowdown"])
        shortfct.sort()
        fct99 = shortfct[int(len(shortfct)*0.99)-1]
        tcpshortfct99.append(fct99)
        
        shortfct = list(shortfctDF["slowdown"])
        shortfct.sort()
        fct95 = shortfct[int(len(shortfct)*0.95)-1]
        shortfct95.append(fct95)
        fct99 = shortfct[int(len(shortfct)*0.99)-1]
        shortfct99.append(fct99)
        fct999 = shortfct[int(len(shortfct)*0.999)-1]
        shortfct999.append(fct999)
        shortfctavg.append(np.mean(shortfct))
        
        pfcDF = pd.read_csv(pfcfile,delimiter=' ')
        numpfc.append(len(pfcDF))
        
        torDF = pd.read_csv(torfile,delimiter=' ')
        lossybuf = torDF["egressOccupancyLossy"]
        losslessbuf = torDF["egressOccupancyLossless"]
        totalbuf = torDF["totalused"]
        lossybuf = list(100*lossybuf/buffer)
        losslessbuf = list(100*losslessbuf/buffer)
        totalbuf = list(100*totalbuf/buffer)
        lossybuf.sort()
        losslessbuf.sort()
        totalbuf.sort()
        lossy.append(lossybuf[int(len(lossybuf)*0.99)])
        lossless.append(losslessbuf[int(len(lossybuf)*0.99)])
        total.append(totalbuf[int(len(lossybuf)*0.99)])
        
        longfctDF = fctDF[(fctDF["flowsize"]>1000000)&(fctDF["priority"])==1]
        longfct = list(longfctDF["slowdown"])
        longfct.sort()
        longfctav.append(np.mean(longfct))
        
        medfctDF = fctDF[(fctDF["flowsize"]<1000000)&(fctDF["flowsize"]>100000)&(fctDF["priority"])==1]
        medfct = list(longfctDF["slowdown"])
        medfct.sort()
        medfctav.append(np.mean(medfct))
        
        # Add data row to output table
        tcp_load_data.append([float(tcpload), names[str(alg)], shortfctavg[-1], numpfc[-1], tcpshortfct99[-1], lossless[-1], lossy[-1]])

# Write results_sigcomm to CSV
write_experiment_results_sigcomm_to_csv(
    "Impact of TCP Load on Performance Metrics", 
    tcp_load_headers, 
    tcp_load_data,
    "tcp_load_impact.csv"
)


# EXPERIMENT 2: RDMA Burst Size Impact
# ===================================

loads=["0.2","0.4","0.6","0.8"]
loadsint=[0.2,0.4,0.6,0.8]
bursts=["500000", "1000000","1500000", "2000000"]

rdmacc=str(DCQCNCC)
tcpcc=str(DCTCP)
tcpburst="0"
tcpload="0.8"
egresslossyFrac="0.8"
gamma="0.999"
rdmaload="0"

# Prepare headers and data for RDMA burst size experiment
rdma_burst_headers = ["RDMA Burst Size", "Algorithm", "Short FCT Avg", "PFC Pauses", "TCP Short FCT 99%", "Lossless Buffer (%)", "Lossy Buffer (%)"]
rdma_burst_data = []

for rdmaburst in bursts:
    shortfct95=list()
    shortfct99=list()
    shortfct999=list()
    shortfctavg=list()
    tcpshortfct99=list()
    numpfc=list()
    lossy=list()
    lossless=list()
    total=list()
    for alg in algs:
        fctfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.fct'
        torfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.tor'
        outfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.out'
        pfcfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.pfc'
        
        fctDF = pd.read_csv(fctfile,delimiter=' ')
        shortfctDF = fctDF[(fctDF["incastflow"]==1)&(fctDF["priority"]==3)]
        
        tcpshortfctDF = fctDF[(fctDF["flowsize"]<100000)&(fctDF["priority"]==1)]
        shortfct = list(tcpshortfctDF["slowdown"])
        shortfct.sort()
        fct99 = shortfct[int(len(shortfct)*0.99)]
        tcpshortfct99.append(fct99)
        
        shortfct = list(shortfctDF["slowdown"])
        shortfct.sort()
        if len(shortfct)>0:
            fct95 = shortfct[int(len(shortfct)*0.95)-1]
            fct99 = shortfct[int(len(shortfct)*0.99)-1]
            fct999 = shortfct[int(len(shortfct)*0.999)-1]
        else:
            fct95=0
            fct99=0
            fct999=0
        shortfct99.append(fct99)
        shortfct95.append(fct95)
        shortfct999.append(fct999)
        shortfctavg.append(np.mean(shortfct))
        
        pfcDF = pd.read_csv(pfcfile,delimiter=' ')
        numpfc.append(len(pfcDF))
        
        torDF = pd.read_csv(torfile,delimiter=' ')
        lossybuf = torDF["egressOccupancyLossy"]
        losslessbuf = torDF["egressOccupancyLossless"]
        totalbuf = torDF["totalused"]
        lossybuf = list(100*lossybuf/buffer)
        losslessbuf = list(100*losslessbuf/buffer)
        totalbuf = list(100*totalbuf/buffer)
        lossybuf.sort()
        losslessbuf.sort()
        totalbuf.sort()
        lossy.append(lossybuf[int(len(lossybuf)*0.99)])
        lossless.append(losslessbuf[int(len(lossybuf)*0.99)])
        total.append(totalbuf[int(len(lossybuf)*0.99)])

        # Add data row to output table
        rdma_burst_data.append([int(rdmaburst), names[str(alg)], shortfctavg[-1], numpfc[-1], tcpshortfct99[-1], lossless[-1], lossy[-1]])

# Write results_sigcomm to CSV
write_experiment_results_sigcomm_to_csv(
    "Impact of RDMA Burst Size on Performance Metrics", 
    rdma_burst_headers, 
    rdma_burst_data,
    "rdma_burst_impact.csv"
)


# EXPERIMENT 3: RDMA Load Impact
# =============================

loads=["0.2","0.4","0.6","0.8"]
loadsint=[0.2,0.4,0.6,0.8]
bursts=["500000", "1000000","1500000", "2000000"]

rdmacc=str(INTCC)
tcpcc=str(DCTCP)
rdmaburst="0"
tcpload="0"
egresslossyFrac="0.8"
gamma="0.999"
tcpburst="1500000"

# Prepare headers and data for RDMA load experiment
rdma_load_headers = ["RDMA Load", "Algorithm", "Short FCT Avg", "PFC Pauses", "RDMA Short FCT 99%", "Lossless Buffer (%)", "Lossy Buffer (%)"]
rdma_load_data = []

for rdmaload in loads:
    shortfct95=list()
    shortfct99=list()
    shortfct999=list()
    shortfctavg=list()
    rdmashortfct99=list()
    rdmalongfctav=list()
    numpfc=list()
    lossy=list()
    lossless=list()
    total=list()
    for alg in algs:
        fctfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.fct'
        torfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.tor'
        outfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.out'
        pfcfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.pfc'
        
        fctDF = pd.read_csv(fctfile,delimiter=' ')
        shortfctDF = fctDF[(fctDF["incastflow"]==1)&(fctDF["priority"]==1)] # fctDF[(fctDF["flowsize"]<100000)&(fctDF["priority"]==3)] #
        
        rdmashortfctDF = fctDF[(fctDF["flowsize"]<100000)&(fctDF["priority"]==3)]
        shortfct = list(rdmashortfctDF["slowdown"])
        shortfct.sort()
        fct99 = shortfct[int(len(shortfct)*0.99)]
        rdmashortfct99.append(fct99)
        
        rdmashortfctDF = fctDF[(fctDF["flowsize"]>1000000)&(fctDF["priority"]==3)]
        shortfct = list(rdmashortfctDF["slowdown"])
        shortfct.sort()
        fct = np.median(shortfct)
        rdmalongfctav.append(fct)
        
        shortfct = list(shortfctDF["slowdown"])
        shortfct.sort()
        if len(shortfct)>0:
            fct95 = shortfct[int(len(shortfct)*0.95)]
            fct99 = shortfct[int(len(shortfct)*0.99)]
            fct999 = shortfct[int(len(shortfct)*0.999)]
        else:
            fct95=0
            fct99=0
            fct999=0
        shortfct99.append(fct99)
        shortfct95.append(fct95)
        shortfct999.append(fct999)
        shortfctavg.append(np.mean(shortfct))
        
        pfcDF = pd.read_csv(pfcfile,delimiter=' ')
        numpfc.append(len(pfcDF))
        
        torDF = pd.read_csv(torfile,delimiter=' ')
        lossybuf = torDF["egressOccupancyLossy"]
        losslessbuf = torDF["egressOccupancyLossless"]
        totalbuf = torDF["totalused"]
        lossybuf = list(100*lossybuf/buffer)
        losslessbuf = list(100*losslessbuf/buffer)
        totalbuf = list(100*totalbuf/buffer)
        lossybuf.sort()
        losslessbuf.sort()
        totalbuf.sort()
        lossy.append(lossybuf[int(len(lossybuf)*0.99)])
        lossless.append(losslessbuf[int(len(lossybuf)*0.99)])
        total.append(totalbuf[int(len(lossybuf)*0.99)])

        # Add data row to output table
        rdma_load_data.append([float(rdmaload), names[str(alg)], shortfctavg[-1], numpfc[-1], rdmashortfct99[-1], lossless[-1], lossy[-1]])

# Write results_sigcomm to CSV
write_experiment_results_sigcomm_to_csv(
    "Impact of RDMA Load on Performance Metrics", 
    rdma_load_headers, 
    rdma_load_data,
    "rdma_load_impact.csv"
)


# EXPERIMENT 4: TCP Burst Size Impact
# ==================================

loads=["0.2","0.4","0.6","0.8"]
loadsint=[0.2,0.4,0.6,0.8]

rdmacc=str(INTCC)
tcpcc=str(DCTCP)
tcpload="0"
egresslossyFrac="0.8"
gamma="0.999"

rdmaload="0.8"
rdmaburst="0"

# Prepare headers and data for TCP burst size experiment
tcp_burst_headers = ["TCP Burst Size", "Algorithm", "Short FCT Avg", "PFC Pauses", "RDMA Short FCT 99%", "Lossless Buffer (%)", "Lossy Buffer (%)"]
tcp_burst_data = []

burststemp=["12500","500000", "1000000","1500000"]
for tcpburst in burststemp:
    shortfct95=list()
    shortfct99=list()
    shortfct999=list()
    shortfctavg=list()
    rdmashortfct99=list()
    rdmalongfctav=list()
    numpfc=list()
    lossy=list()
    lossless=list()
    total=list()
    for alg in algs:
        fctfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.fct'
        torfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.tor'
        outfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.out'
        pfcfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.pfc'
        
        fctDF = pd.read_csv(fctfile,delimiter=' ')
        shortfctDF = fctDF[(fctDF["incastflow"]==1)&(fctDF["priority"]==1)] #fctDF[(fctDF["flowsize"]<100000)&(fctDF["priority"]==3)]
        
        rdmashortfctDF = fctDF[(fctDF["flowsize"]<100000)&(fctDF["priority"]==3)]
        shortfct = list(rdmashortfctDF["slowdown"])
        shortfct.sort()
        fct99 = shortfct[int(len(shortfct)*0.99)]
        rdmashortfct99.append(fct99)
        
        rdmashortfctDF = fctDF[(fctDF["flowsize"]>1000000)&(fctDF["priority"]==3)]
        shortfct = list(rdmashortfctDF["slowdown"])
        shortfct.sort()
        fct =  np.median(shortfct)
        rdmalongfctav.append(fct)
        
        shortfct = list(shortfctDF["slowdown"])
        shortfct.sort()
        if len(shortfct)>0:
            fct95 = shortfct[int(len(shortfct)*0.95)]
            fct99 = shortfct[int(len(shortfct)*0.99)]
            fct999 = shortfct[int(len(shortfct)*0.999)]
        else:
            fct95=0
            fct99=0
            fct999=0
        shortfct99.append(fct99)
        shortfct95.append(fct95)
        shortfct999.append(fct999)
        shortfctavg.append(np.mean(shortfct))
        
        pfcDF = pd.read_csv(pfcfile,delimiter=' ')
        numpfc.append(len(pfcDF))
        
        torDF = pd.read_csv(torfile,delimiter=' ')
        lossybuf = torDF["egressOccupancyLossy"]
        losslessbuf = torDF["egressOccupancyLossless"]
        totalbuf = torDF["totalused"]
        lossybuf = list(100*lossybuf/buffer)
        losslessbuf = list(100*losslessbuf/buffer)
        totalbuf = list(100*totalbuf/buffer)
        lossybuf.sort()
        losslessbuf.sort()
        totalbuf.sort()
        lossy.append(lossybuf[int(len(lossybuf)*0.99)])
        lossless.append(losslessbuf[int(len(lossybuf)*0.99)])
        total.append(totalbuf[int(len(lossybuf)*0.99)])

        # Add data row to output table
        tcp_burst_data.append([int(tcpburst), names[str(alg)], shortfctavg[-1], numpfc[-1], rdmashortfct99[-1], lossless[-1], lossy[-1]])

# Write results_sigcomm to CSV
write_experiment_results_sigcomm_to_csv(
    "Impact of TCP Burst Size on Performance Metrics", 
    tcp_burst_headers, 
    tcp_burst_data,
    "tcp_burst_impact.csv"
)


# EXPERIMENT 5: Effect of Gamma Parameter (Low-Pass Filter)
# ========================================================

plt.rcParams.update({'font.size': 14})

loads=["0.2","0.4","0.6","0.8"]
loadsint=[0.2,0.4,0.6,0.8]

bursts=["500000", "1000000","1500000", "2000000", "2500000"]

rdmacc=str(DCQCNCC)
tcpcc=str(DCTCP)
rdmaburst="2000000"
tcpburst="0"
egresslossyFrac="0.8"
gamma="0.999"
tcpload="0"
rdmaload="0.8"

fig0,ax0 = plt.subplots(1,1,figsize=(6,3))
fig1,ax1 = plt.subplots(1,1,figsize=(6,3))
fig2,ax2 = plt.subplots(1,1,figsize=(6,3))
fig3,ax3 = plt.subplots(1,1,figsize=(6,3))
fig4,ax4 = plt.subplots(1,1,figsize=(6,3))

# Prepare headers and data for gamma parameter impact experiment
gamma_headers = ["γ Value", "Average FCT for Incast Flows", "Number of PFC Pauses"]
gamma_data = []

alg=str(REVERIE)
numpfc=list()
shortfct95=list()
shortfct99=list()
shortfct999=list()
shortfctavg=list()

for gamma in ["0.8","0.9","0.99","0.999","0.999999"]:
    fctfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.fct'
    
    fctDF = pd.read_csv(fctfile,delimiter=' ')
    shortfctDF = fctDF[(fctDF["incastflow"]==1)&(fctDF["priority"]==3)] #fctDF[(fctDF["flowsize"]<100000)&(fctDF["priority"]==3)]   
    shortfct = list(shortfctDF["slowdown"])
    shortfct.sort()
    if len(shortfct)>0:
        fct95 = shortfct[int(len(shortfct)*0.95)]
        fct99 = shortfct[int(len(shortfct)*0.99)]
        fct999 = shortfct[int(len(shortfct)*0.999)]
    else:
        fct95=0
        fct99=0
        fct999=0
    shortfct99.append(fct99)
    shortfct95.append(fct95)
    shortfct999.append(fct999)
    shortfctavg.append(np.mean(shortfct))
    
    pfcfile = dump+"evaluation-"+alg+'-'+rdmacc+'-'+tcpcc+'-'+rdmaload+'-'+tcpload+'-'+rdmaburst+'-'+tcpburst+'-'+egresslossyFrac+'-'+gamma+'.pfc'
    pfcDF = pd.read_csv(pfcfile,delimiter=' ')
    numpfc.append(len(pfcDF))

    # Add data row to output table
    gamma_data.append([gamma, shortfctavg[-1], numpfc[-1]])

# Write results_sigcomm to CSV
write_experiment_results_sigcomm_to_csv(
    "Impact of Low-Pass Filter Parameter on Reverie Performance", 
    gamma_headers, 
    gamma_data,
    "gamma_parameter_impact.csv"
)
