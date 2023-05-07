import sys
sys.path.append(".")
import visualization

prefix = "/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCFM/sample_logs/"
#ocellist = ["jsonocel/order_process.jsonocel","jsonocel/p2p-normal.jsonocel","csv/BPI2017-Final.csv"]
ocellist = ["csv/BPI2017-Final.csv"]
print(visualization.Drawcomparisontable([prefix+str for str in ocellist],[],automodel=True))