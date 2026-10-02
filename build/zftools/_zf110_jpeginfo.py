import struct,sys,io
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
p=r"E:\PotatoST\build\用户素材\油桶.jpg"
b=open(p,'rb').read()
print("字节数",len(b))
# JPEG 内嵌 ICC_PROFILE 段 (APP2 0xE2) 扫描
i=2; found=[]
while i+4<=len(b):
    if b[i]!=0xFF: i+=1; continue
    m=b[i+1]
    if m in (0xD8,0xD9) or 0xD0<=m<=0xD7: i+=2; continue
    if i+4>len(b): break
    ln=struct.unpack(">H",b[i+2:i+4])[0]
    seg=b[i+4:i+2+ln]
    if m==0xE2 and seg[:11]==b"ICC_PROFILE": found.append(("APP2 ICC",seg[12:20]))
    if m==0xEE: found.append(("APP14 Adobe",seg[0:12]))
    if m in (0xC0,0xC1,0xC2): found.append(("SOF",seg[0:6]))
    i+=2+ln
for k,v in found: print(k,v)
print("色彩空间线索: APP14" , "无(纯 JFIF)" if not any(k=="APP14 Adobe" for k,_ in found) else "有")
