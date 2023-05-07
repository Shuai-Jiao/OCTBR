import sys
sys.path.append(".")
import visualization

prefix = "/Users/jiao.shuai.1998.12.01outlook.com/Documents/OCFM/sample_logs/"
ocellist = ["jsonocel/order_process.jsonocel"]
print(visualization.Drawcomparisontable(ocellist,[],automodel=True))