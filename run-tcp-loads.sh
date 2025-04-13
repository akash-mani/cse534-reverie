# ./waf --run "reverie-evaluation-sigcomm2023 --powertcp=true --bufferalgIngress=101 --bufferalgEgress=101 --rdmacc=3 --rdmaload=0.2 --rdmarequestSize=0 --rdmaqueryRequestRate=2 --tcpload=0 --tcpcc=2 --enableEcn=true --tcpqueryRequestRate=2 --tcprequestSize=1500000 --egressLossyShare=0.8 --bufferModel=sonic --gamma=0.999 --START_TIME=1 --END_TIME=4 --FLOW_LAUNCH_END_TIME=3 --buffersize=2560000 --fctOutFile=dump_sigcomm/evaluation-101-3-2-0.2-0-0-1500000-0.8-0.999.fct --torOutFile=dump_sigcomm/evaluation-101-3-2-0.2-0-0-1500000-0.8-0.999.tor --alphasFile=/path/to/alphas --pfcOutFile=dump_sigcomm/evaluation-101-3-2-0.2-0-0-1500000-0.8-0.999.pfc"

# ./waf --run "reverie-evaluation-sigcomm2023 --powertcp=true --bufferalgIngress=101 --bufferalgEgress=101 --rdmacc=3 --rdmaload=0.4 --rdmarequestSize=0 --rdmaqueryRequestRate=2 --tcpload=0 --tcpcc=2 --enableEcn=true --tcpqueryRequestRate=2 --tcprequestSize=1500000 --egressLossyShare=0.8 --bufferModel=sonic --gamma=0.999 --START_TIME=1 --END_TIME=4 --FLOW_LAUNCH_END_TIME=3 --buffersize=2560000 --fctOutFile=dump_sigcomm/evaluation-101-3-2-0.4-0-0-1500000-0.8-0.999.fct --torOutFile=dump_sigcomm/evaluation-101-3-2-0.4-0-0-1500000-0.8-0.999.tor --alphasFile=/path/to/alphas --pfcOutFile=dump_sigcomm/evaluation-101-3-2-0.4-0-0-1500000-0.8-0.999.pfc"

# ./waf --run "reverie-evaluation-sigcomm2023 --powertcp=true --bufferalgIngress=101 --bufferalgEgress=101 --rdmacc=3 --rdmaload=0.6 --rdmarequestSize=0 --rdmaqueryRequestRate=2 --tcpload=0 --tcpcc=2 --enableEcn=true --tcpqueryRequestRate=2 --tcprequestSize=1500000 --egressLossyShare=0.8 --bufferModel=sonic --gamma=0.999 --START_TIME=1 --END_TIME=4 --FLOW_LAUNCH_END_TIME=3 --buffersize=2560000 --fctOutFile=dump_sigcomm/evaluation-101-3-2-0.6-0-0-1500000-0.8-0.999.fct --torOutFile=dump_sigcomm/evaluation-101-3-2-0.6-0-0-1500000-0.8-0.999.tor --alphasFile=/path/to/alphas --pfcOutFile=dump_sigcomm/evaluation-101-3-2-0.6-0-0-1500000-0.8-0.999.pfc"

# ./waf --run "reverie-evaluation-sigcomm2023 --powertcp=true --bufferalgIngress=101 --bufferalgEgress=101 --rdmacc=3 --rdmaload=0.8 --rdmarequestSize=0 --rdmaqueryRequestRate=2 --tcpload=0 --tcpcc=2 --enableEcn=true --tcpqueryRequestRate=2 --tcprequestSize=1500000 --egressLossyShare=0.8 --bufferModel=sonic --gamma=0.999 --START_TIME=1 --END_TIME=4 --FLOW_LAUNCH_END_TIME=3 --buffersize=2560000 --fctOutFile=dump_sigcomm/evaluation-101-3-2-0.8-0-0-1500000-0.8-0.999.fct --torOutFile=dump_sigcomm/evaluation-101-3-2-0.8-0-0-1500000-0.8-0.999.tor --alphasFile=/path/to/alphas --pfcOutFile=dump_sigcomm/evaluation-101-3-2-0.8-0-0-1500000-0.8-0.999.pfc"

# # Repeat for BUFFER_ALGS=110 (ABM) and BUFFER_ALGS=111 (REVERIE)
# # For brevity, only the first set of commands is shown.

# ------------------------
# Primary Variable: RDMA load (0.2-0.8)
# Fixed: TCP request size at 1.5M bytes, no TCP load
# Purpose: Examines how increasing RDMA background load affects TCP burst handling

source config.sh
DIR=$(pwd)
DUMP_DIR=$DIR/dump_sigcomm
RESULTS_DIR=$DIR/results_sigcomm

if [ ! -d "$DUMP_DIR" ];then
	mkdir $DUMP_DIR
fi
if [ ! -d "$RESULTS_DIR" ];then
	mkdir $RESULTS_DIR
fi

cd $NS3

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


NUM=0

# BUFFER_ALGS=($DT $FAB $ABM "reverie")
BUFFER_ALGS=($DT $ABM $REVERIE)

BURST_SIZES=(12500 500000 1000000 1500000 2000000)

LOADS=(0.2 0.4 0.6 0.8)

egresslossyFrac=0.8

gamma=0.999

START_TIME=1
END_TIME=4
FLOW_LAUNCH_END_TIME=3
BUFFER_PER_PORT_PER_GBPS=5.12 # in KiloBytes per port per Gbps
BUFFERSIZE=$(python3 -c "print(20*25*1000*$BUFFER_PER_PORT_PER_GBPS)") # in Bytes
ALPHAFILE=$DIR/alphas

EXP=$1

RDMAREQRATE=2
TCPREQRATE=2

############################################################################
######### 
tcpload=0
tcpburst=1500000
rdmaburst=0
RDMACC=$INTCC
TCPCC=$DCTCP
for rdmaload in ${LOADS[@]};do
	# tcpload=$(python3 -c "print('%.1f'%(0.8-$rdmaload))")
	for alg in ${BUFFER_ALGS[@]};do
		if [[ $alg != $REVERIE ]];then
			BUFFERMODEL="sonic"
		else
			BUFFERMODEL="reverie"
		fi
		while [[ $(ps aux | grep reverie-evaluation-sigcomm2023-optimized | wc -l) -gt $N_CORES ]];do
			sleep 30;
			echo "waiting for cores, $N_CORES running..."
		done
		FCTFILE=$DUMP_DIR/evaluation-$alg-$RDMACC-$TCPCC-$rdmaload-$tcpload-$rdmaburst-$tcpburst-$egresslossyFrac-$gamma.fct
		TORFILE=$DUMP_DIR/evaluation-$alg-$RDMACC-$TCPCC-$rdmaload-$tcpload-$rdmaburst-$tcpburst-$egresslossyFrac-$gamma.tor
		DUMPFILE=$DUMP_DIR/evaluation-$alg-$RDMACC-$TCPCC-$rdmaload-$tcpload-$rdmaburst-$tcpburst-$egresslossyFrac-$gamma.out
		PFCFILE=$DUMP_DIR/evaluation-$alg-$RDMACC-$TCPCC-$rdmaload-$tcpload-$rdmaburst-$tcpburst-$egresslossyFrac-$gamma.pfc
		echo $FCTFILE
		if [ -f "$FCTFILE" ]; then
			echo "Skipping: $FCTFILE already exists"
			NUM=$(( $NUM+1 ))
			continue
		fi
		if [[ $EXP == 1 ]];then
			(time ./waf --run "reverie-evaluation-sigcomm2023 --powertcp=true --bufferalgIngress=$alg --bufferalgEgress=$alg --rdmacc=$RDMACC --rdmaload=$rdmaload --rdmarequestSize=$rdmaburst --rdmaqueryRequestRate=$RDMAREQRATE --tcpload=$tcpload --tcpcc=$TCPCC --enableEcn=true --tcpqueryRequestRate=$TCPREQRATE --tcprequestSize=$tcpburst --egressLossyShare=$egresslossyFrac --bufferModel=$BUFFERMODEL --gamma=$gamma --START_TIME=$START_TIME --END_TIME=$END_TIME --FLOW_LAUNCH_END_TIME=$FLOW_LAUNCH_END_TIME --buffersize=$BUFFERSIZE --fctOutFile=$FCTFILE --torOutFile=$TORFILE --alphasFile=$ALPHAFILE --pfcOutFile=$PFCFILE" > $DUMPFILE 2> $DUMPFILE)&
			sleep 5
		fi
		NUM=$(( $NUM+1  ))
	done
done

echo "Total $NUM experiments"
