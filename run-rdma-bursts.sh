# ./waf --run "reverie-evaluation-sigcomm2023 --bufferalgIngress=101 --bufferalgEgress=101 --rdmacc=1 --rdmaload=0 --rdmarequestSize=0 --rdmaqueryRequestRate=2 --tcpload=0.8 --tcpcc=2 --enableEcn=true --tcpqueryRequestRate=2 --tcprequestSize=0 --egressLossyShare=0.8 --bufferModel=sonic --gamma=0.999 --START_TIME=1 --END_TIME=4 --FLOW_LAUNCH_END_TIME=3 --buffersize=2560000 --fctOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-0-0-0.8-0.999.fct --torOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-0-0-0.8-0.999.tor --alphasFile=/path/to/alphas --pfcOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-0-0-0.8-0.999.pfc"

# ./waf --run "reverie-evaluation-sigcomm2023 --bufferalgIngress=101 --bufferalgEgress=101 --rdmacc=1 --rdmaload=0 --rdmarequestSize=500000 --rdmaqueryRequestRate=2 --tcpload=0.8 --tcpcc=2 --enableEcn=true --tcpqueryRequestRate=2 --tcprequestSize=0 --egressLossyShare=0.8 --bufferModel=sonic --gamma=0.999 --START_TIME=1 --END_TIME=4 --FLOW_LAUNCH_END_TIME=3 --buffersize=2560000 --fctOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-500000-0-0.8-0.999.fct --torOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-500000-0-0.8-0.999.tor --alphasFile=/path/to/alphas --pfcOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-500000-0-0.8-0.999.pfc"

# ./waf --run "reverie-evaluation-sigcomm2023 --bufferalgIngress=101 --bufferalgEgress=101 --rdmacc=1 --rdmaload=0 --rdmarequestSize=1000000 --rdmaqueryRequestRate=2 --tcpload=0.8 --tcpcc=2 --enableEcn=true --tcpqueryRequestRate=2 --tcprequestSize=0 --egressLossyShare=0.8 --bufferModel=sonic --gamma=0.999 --START_TIME=1 --END_TIME=4 --FLOW_LAUNCH_END_TIME=3 --buffersize=2560000 --fctOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-1000000-0-0.8-0.999.fct --torOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-1000000-0-0.8-0.999.tor --alphasFile=/path/to/alphas --pfcOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-1000000-0-0.8-0.999.pfc"

# ./waf --run "reverie-evaluation-sigcomm2023 --bufferalgIngress=101 --bufferalgEgress=101 --rdmacc=1 --rdmaload=0 --rdmarequestSize=1500000 --rdmaqueryRequestRate=2 --tcpload=0.8 --tcpcc=2 --enableEcn=true --tcpqueryRequestRate=2 --tcprequestSize=0 --egressLossyShare=0.8 --bufferModel=sonic --gamma=0.999 --START_TIME=1 --END_TIME=4 --FLOW_LAUNCH_END_TIME=3 --buffersize=2560000 --fctOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-1500000-0-0.8-0.999.fct --torOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-1500000-0-0.8-0.999.tor --alphasFile=/path/to/alphas --pfcOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-1500000-0-0.8-0.999.pfc"

# ./waf --run "reverie-evaluation-sigcomm2023 --bufferalgIngress=101 --bufferalgEgress=101 --rdmacc=1 --rdmaload=0 --rdmarequestSize=2500000 --rdmaqueryRequestRate=2 --tcpload=0.8 --tcpcc=2 --enableEcn=true --tcpqueryRequestRate=2 --tcprequestSize=0 --egressLossyShare=0.8 --bufferModel=sonic --gamma=0.999 --START_TIME=1 --END_TIME=4 --FLOW_LAUNCH_END_TIME=3 --buffersize=2560000 --fctOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-2500000-0-0.8-0.999.fct --torOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-2500000-0-0.8-0.999.tor --alphasFile=/path/to/alphas --pfcOutFile=dump_sigcomm/evaluation-101-1-2-0-0.8-2500000-0-0.8-0.999.pfc"

# # Repeat the above pattern for BUFFER_ALGS=110 (ABM) and BUFFER_ALGS=111 (REVERIE), adjusting BUFFERMODEL accordingly.
# ------------------------
# Primary Variable: RDMA request size (0-2.5M bytes)
# Fixed: TCP load at 0.8, no RDMA load
# Purpose: Tests how buffer algorithms handle different sized RDMA bursts while TCP traffic is heavily loaded

source config.sh
DIR=$(pwd)
DUMP_DIR=$DIR/dumps
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

BURST_SIZES=(0 500000 1000000 1500000 2000000 2500000)

LOADS=(0 0.2 0.4 0.6 0.8)

egresslossyFrac=0.8

gamma=0.999

START_TIME=1
END_TIME=4
FLOW_LAUNCH_END_TIME=3
BUFFER_PER_PORT_PER_GBPS=5.12 # in KiloBytes per port per Gbps
BUFFERSIZE=$(python3 -c "print(10*25*1000*$BUFFER_PER_PORT_PER_GBPS)") # in Bytes
ALPHAFILE=$DIR/alphas

EXP=$1

RDMAREQRATE=2
TCPREQRATE=2

############################################################################
###### Pure RDMA low load, across bursts with default DCQCN
rdmaload=0
tcpload=0.8
tcpburst=0
RDMACC=$DCQCNCC
TCPCC=$CUBIC
for rdmaburst in ${BURST_SIZES[@]};do
	if [[ $rdmaburst == 2000000 ]];then
		continue;
	fi
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
			(time ./waf --run "reverie-evaluation-sigcomm2023 --bufferalgIngress=$alg --bufferalgEgress=$alg --rdmacc=$RDMACC --rdmaload=$rdmaload --rdmarequestSize=$rdmaburst --rdmaqueryRequestRate=$RDMAREQRATE --tcpload=$tcpload --tcpcc=$TCPCC --enableEcn=true --tcpqueryRequestRate=$TCPREQRATE --tcprequestSize=$tcpburst --egressLossyShare=$egresslossyFrac --bufferModel=$BUFFERMODEL --gamma=$gamma --START_TIME=$START_TIME --END_TIME=$END_TIME --FLOW_LAUNCH_END_TIME=$FLOW_LAUNCH_END_TIME --buffersize=$BUFFERSIZE --fctOutFile=$FCTFILE --torOutFile=$TORFILE --alphasFile=$ALPHAFILE --pfcOutFile=$PFCFILE" > $DUMPFILE 2> $DUMPFILE)&
			sleep 5
		fi
		NUM=$(( $NUM+1  ))
	done
done

echo "Total $NUM experiments"