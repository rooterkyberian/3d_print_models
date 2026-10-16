"""Dimensioned section extracted from final STL, and rope channel diagram.

Usage: python section.py [DEPTHS ...]; draws every built variant by default.
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyBboxPatch,Polygon
from variants import built
def section(p):
 c=json.loads((p/'parameters.json').read_text())
 W,H,ZMAX=c['dimensions_mm'];BACK=c['floor_z_mm'];PW,PH=c['pocket_size_mm']
 RX,RR,ER=c['rope_x_mm'],c['channel_radius_mm'],c['exit_radius_mm']
 raw=(p/(c['name']+'.stl')).read_bytes();r=np.frombuffer(raw,dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')]),offset=84)
 v=r['v'].astype(float)
 segments=[]
 for t in v[(v[:,:,0].min(axis=1)<=0)&(v[:,:,0].max(axis=1)>=0)]:
  points=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   if abs(t[i,0])<1e-9:points.append(t[i])
   if t[i,0]*t[j,0]<0:points.append(t[i]+(t[j]-t[i])*(-t[i,0])/(t[j,0]-t[i,0]))
  if len(points)<2:continue
  points=np.unique(np.round(points,7),axis=0)
  if len(points)==2:segments.append(points[:,[2,1]])
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
 # Scale figure height with the board so both panels keep equal aspect;
 # margins are fixed in inches for the titles and footnote.
 fh=2+(H+43)*6/193
 fig,(ax,rx)=plt.subplots(1,2,figsize=(9,fh),gridspec_kw={'width_ratios':[.7,1.7]})
 fig.patch.set_facecolor('#faf9f6')
 ax.set_facecolor('#faf9f6');rx.set_facecolor('#faf9f6')
 ax.add_collection(LineCollection(segments,colors='#795921',linewidths=1.5))
 for yc,lo,hi in c['pockets']:
  for yy,d in [(yc-PH/2-4,lo),(yc+PH/2+4,hi)]:
   ax.annotate('',xy=(BACK+d,yy),xytext=(BACK,yy),arrowprops={'arrowstyle':'<->','color':'#185da2','linewidth':1})
   ax.text(BACK+d/2,yy+1.5,f'{d:g} mm',ha='center',va='bottom',fontsize=8,color='#185da2')
 ax.set_xlim(-3,ZMAX+5);ax.set_ylim(-H/2-6,H/2+6);ax.set_aspect('equal');ax.set_xlabel('Thickness Z [mm]');ax.set_ylabel('Height Y [mm]');ax.set_title('STL section\nthrough pocket centre',fontsize=12,pad=16)
 ax.set_xticks(range(0,int(ZMAX)+1,10));ax.grid(alpha=.15)
 # Front view outlines, nominal (corner cuts unrounded): full width below the
 # rope axis (light).
 CY=H/2-c['collar_length_mm'];SH=c['shelf_x_mm'];CH=c['corner_chamfer_mm'];TK=c['track_depth_mm']
 lo=[(W/2-CH,-H/2),(W/2,-H/2+CH)];hi=[(W/2,H/2-CH),(W/2-CH,H/2)]
 mirror=lambda right:np.concatenate((right,right[::-1]*[-1,1]))
 rx.add_patch(Polygon(mirror(np.array(lo+hi)),closed=True,facecolor='#f6ead0',edgecolor='#795921'))
 # Front level: cut back to the shelf wall between the collars, and to the
 # rope axis in the collars, where a tube encloses the rope (mid tone).
 k=RX-(W/2-CH);TO=min(c['tube_outer_radius_mm'],W/2-RX)
 rx.add_patch(Polygon(mirror(np.array([(W/2-CH,-H/2),(RX,-H/2+k),(RX,-CY),(SH,-CY),(SH,CY),(RX,CY),(RX,H/2-k),(W/2-CH,H/2)])),closed=True,facecolor='#ecd6a3',edgecolor='#795921'))
 for sx in [-1,1]:
  for sy in [-1,1]:
   rx.add_patch(Polygon([(sx*RX,sy*CY),(sx*(RX+TO),sy*CY),(sx*(RX+TO),sy*(H/2-k-TO)),(sx*RX,sy*(H/2-k))],closed=True,facecolor='#e2c88f',edgecolor='#795921'))
 for yc,lo,hi in c['pockets']:
  rx.add_patch(FancyBboxPatch((-PW/2,yc-PH/2),PW,PH,boxstyle='round,pad=0,rounding_size=5',facecolor='#faf9f6',edgecolor='#b08d4b'))
  LU=c['label_offset_mm']
  rx.text(0,yc-PH/2-LU,f'{lo:g}',ha='center',va='center',fontsize=10);rx.text(0,yc+PH/2+LU,f'{hi:g}',ha='center',va='center',rotation=180,fontsize=10)
 # Channel axes: solid over the open seat, dashed inside the collars and past
 # both ends, where the rope can leave straight either way up.
 for x in [-RX,RX]:
  rx.plot([x,x],[-CY,CY],color='#185da2',lw=2)
  for sy in [-1,1]:rx.plot([x,x],[sy*CY,sy*(H/2+8)],color='#185da2',lw=2,ls='--')
 # Inner side of each exit: round of ER, running on as the track across the
 # end face.
 Rb=ER+RR+c['exit_sweep_oversize_mm']
 for sy in [-1,1]:
  for sx in [-1,1]:
   cx,cy=sx*(RX-Rb),sy*(H/2-TK-ER)
   a=np.linspace(0,np.pi/2,60);rx.plot(cx+sx*ER*np.cos(a),cy+sy*ER*np.sin(a),color='#185da2',lw=2.5)
  rx.plot([-(RX-Rb),RX-Rb],[sy*(H/2-TK)]*2,color='#185da2',lw=2.5)
 cx,cy=RX-Rb,H/2-TK-ER
 rx.annotate(f'R{ER:g} rounded exit',xy=(cx+ER/np.sqrt(2),cy+ER/np.sqrt(2)),xytext=(20,H/2+15),arrowprops={'arrowstyle':'->','color':'#185da2'},color='#185da2',ha='center',fontsize=10)
 rx.set_xlim(-W/2-10,W/2+10);rx.set_ylim(-H/2-19,H/2+24);rx.set_aspect('equal');rx.axis('off');rx.set_title('Rope channels\ntube collars, open seat between',fontsize=12,pad=16)
 rx.text(0,-H/2-14,f'Ø{2*RR:g} mm channel for a Ø{c["cord_diameter_mm"]:g} mm cord, axis at Z={c["rope_z_mm"]:g} mm, see-through end to end\nClosed {c["collar_length_mm"]:g} mm collars (dashed), open seat (solid), {TK:g} mm track across the ends',ha='center',fontsize=9,color='#405367')
 fig.suptitle('Hangboard '+', '.join(f'{lo:g}/{hi:g}' for _,lo,hi in c['pockets'])+' mm',fontsize=15,y=1-.16/fh)
 fig.text(.5,.28/fh,'Nominal dimensions before rounding. Geometry drawing only; load capacity not verified.',ha='center',fontsize=9,color='#555555')
 fig.subplots_adjust(left=.07,right=.98,top=1-1.12/fh,bottom=.88/fh,wspace=.18)
 fig.savefig(p/'section-and-rope.png',dpi=170)
 plt.close(fig)
 print('Saved',p.name,'section-and-rope.png')
for p in built():section(p)
