#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["gmsh", "numpy", "matplotlib", "scipy"]
# ///
"""Linear static FEA of the hangboard: gmsh meshes the STEP, CalculiX solves.

One load case per edge. Fingers press the edge face; a closed rope loop
through the two side channels reacts it. A tensioned rope loads the board
only where it curves, so the rope enters as pressure on the inner wall of the
round turns at the four corners, which turn about Z:
- on the side the fingers pull towards (the sling side) the loop turns 90 deg
  round each corner and cradles the board, pushing sqrt(2)*T per corner;
- on the anchor side the strands leave turning only by the strand angle phi,
  pushing 2*T*sin(phi/2);
with strand tension T = F/(2*cos(phi)). Straight channels carry no load.
Three rope layouts are understood, told apart by parameters.json:
- looped grooves (v5): R13 corner bends join the side channels to open
  grooves on the end faces; the inner wall runs the full 90 deg;
- straight see-through channels whose exits flare inwards with an R9.6 round
  under the loop (v6). That round meets the end face at WALL_END < 90 deg (it
  stops short of tangency), so the rest of the turn bears on that edge; that
  kink load is spread over the last --kink-spread mm of the round;
- straight channels joined at each end by one trough sweep: an EXIT_R round
  in a trough closer to the cord, carrying on as a shallow track across the
  end face, so the full 90 deg turn stays on the round.
Half model (x >= 0) with a symmetry plane. Units N, mm, MPa. Printed flat on
the back, so Z is the layer-stacking direction: S33 is tension across layers.
Rope contact is frictionless, the rope is a fixed load (no contact solve).
With --infill below 100 the part is split as a slicer would: perimeters
within --walls of each layer's outline, solid within --top/--bottom of a
surface above/below, sparse infill elsewhere, smeared into a homogeneous
material (--infill-pattern):
- gyroid: isotropic, stiffness E*density**n. Its stresses are also given
  scaled up by E/E_infill: the stress in its own plastic if its strength
  scales with density as its stiffness does;
- grid: two families of vertical walls at --infill-angle and 90 deg more,
  stacked line on line, each a plane-stress plate of solid plastic. Stiff
  along Z and along the walls, a mechanism under shear across them, where a
  small isotropic stiffness stands in for the walls' bending. The stress in
  the walls follows from the strain.
"""
import argparse,hashlib,json,os,re,shutil,subprocess,time
from pathlib import Path
import numpy as np
import gmsh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,TwoSlopeNorm,Normalize
from matplotlib.tri import Triangulation

here=Path(__file__).parent
ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--step',type=Path,required=True,help='hangboard STEP file')
ap.add_argument('--params',type=Path,help='parameters.json (default: next to --step)')
ap.add_argument('--out',type=Path,help='output directory (default: fea/<variant name>)')
ap.add_argument('--force',type=float,default=1000.,help='finger load per case, N (default 1000 N ~ 102 kg)')
ap.add_argument('--strand-angle',type=float,default=20.,help='rope strand angle from the board axis, deg')
ap.add_argument('--edges',type=int,nargs='*',help='edge depths to run (default: all)')
ap.add_argument('--finger-width',type=float,default=80.,help='loaded width of the edge, mm')
ap.add_argument('--contact-angle',type=float,default=35.,help='rope contact half-angle around the channel wall, deg')
ap.add_argument('--rope-diameter',type=float,help='cord diameter, mm (drawings only; default from parameters.json, else 6)')
ap.add_argument('--kink-spread',type=float,default=2.,help='length of round before its edge that takes the kink load, mm')
ap.add_argument('--fine',type=float,default=.7,help='element size at root fillets and rope bends, mm')
ap.add_argument('--coarse',type=float,default=5.,help='maximum element size, mm')
ap.add_argument('--E',type=float,default=3000.,help="Young's modulus, MPa (stresses barely depend on it)")
ap.add_argument('--nu',type=float,default=.35)
ap.add_argument('--infill',type=float,default=100.,help='sparse infill density, %% (default 100: solid)')
ap.add_argument('--infill-pattern',choices=['gyroid','grid'],default='gyroid')
ap.add_argument('--infill-exponent',type=float,default=1.5,help='gyroid stiffness scales as density**this')
ap.add_argument('--infill-angle',type=float,default=45.,help='grid wall direction from X, deg (PrusaSlicer default 45)')
ap.add_argument('--walls',type=float,default=2.7,help='perimeter thickness, mm (default 6 x 0.45)')
ap.add_argument('--top',type=float,default=1.,help='top solid thickness, mm')
ap.add_argument('--bottom',type=float,default=.8,help='bottom solid thickness, mm')
ap.add_argument('--layer',type=float,default=.2,help='layer height, mm (infill split only)')
a=ap.parse_args()
c=json.loads((a.params or a.step.parent/'parameters.json').read_text())
a.out=a.out or here/'fea'/(c.get('name',a.step.stem).removeprefix('hangboard_')+(f'-{a.infill_pattern}{a.infill:g}' if a.infill<100 else ''))
a.rope_diameter=a.rope_diameter or c.get('cord_diameter_mm',6.)
W,H,_=c['dimensions_mm'];PW,PH=c['pocket_size_mm'];FLOOR=c['floor_z_mm']
RR=c['pocket_root_radius_mm'];ER=c['edge_radius_mm'];RZ=c['rope_z_mm']
# Each corner turn is a torus about Z: centre BC (mirrored by the signs of x
# and y), centreline radius BR, tube radius CR; theta runs from the side
# channel (0) towards the board centre, with wall up to WALL_END.
if 'bend_centerline_radius_mm' in c:
    CR=c['channel_radius_mm'];BR=c['bend_centerline_radius_mm']
    side_x=c['central_width_mm']/2-CR-c['outer_cover_min_mm']
    BC=np.array([side_x-BR,H/2-BR]);WALL_END=90.
elif 'exit_trough_radius_mm' in c:
    CR=c['exit_trough_radius_mm'];BR=c['exit_radius_mm']+CR
    BC=np.array([c['rope_x_mm']-c['channel_radius_mm']-c['exit_sweep_oversize_mm']-c['exit_radius_mm'],
                 H/2-c['track_depth_mm']-c['exit_radius_mm']]);WALL_END=90.
elif 'exit_radius_mm' in c:
    CR=c['channel_radius_mm']+c['exit_sweep_oversize_mm'];BR=c['exit_radius_mm']+CR
    BC=np.array([c['rope_x_mm']-BR,H/2-c['exit_radius_mm']+c['exit_dip_mm']])
    WALL_END=float(np.degrees(np.arcsin((H/2-BC[1])/(BR-CR))))
else:raise SystemExit('unknown rope layout in parameters.json')
KINK_SPREAD=np.degrees(a.kink_spread/(BR-CR))
work=a.out/'work';work.mkdir(parents=True,exist_ok=True)
(a.out/'.gitignore').write_text('work/\n')
# Each pocket gives two edges. The fingers push the face into its bar, along
# +-Y; the depth is the label.
edges=[]
for yc,dlo,dhi in c['pockets']:
    edges+=[dict(depth=round(dlo),face_y=yc-PH/2,push=-1),dict(depth=round(dhi),face_y=yc+PH/2,push=1)]
edges=sorted([e for e in edges if not a.edges or e['depth'] in a.edges],key=lambda e:-e['depth'])
assert edges,'no matching edges'
walls=sorted([-H/2,H/2]+[yc+s*PH/2 for yc,_,_ in c['pockets'] for s in(-1,1)])
for e in edges:
    # The solid bar behind the loaded face: from the face to the next wall.
    nxt=min(w for w in walls if w>e['face_y']+1e-6) if e['push']>0 else max(w for w in walls if w<e['face_y']-1e-6)
    e['bar']=sorted([e['face_y'],nxt])

# ---------------------------------------------------------------- mesh
t0=time.time()
gmsh.initialize();gmsh.option.setNumber('General.Verbosity',2)
occ=gmsh.model.occ
occ.importShapes(str(a.step))
occ.intersect(occ.getEntities(3),[(3,occ.addBox(0,-H,-5,W,2*H,60))])
occ.synchronize()
sym,refine=[],[]
faces={}
for _,t in gmsh.model.getEntities(2):
    typ=gmsh.model.getType(2,t);bb=gmsh.model.getBoundingBox(2,t)
    if typ=='Plane' and bb[3]<1e-6:sym.append(t)
    if typ=='Plane' and abs(bb[1]-bb[4])<1e-6 and abs(bb[2]-FLOOR-RR)<1e-3:faces[round(bb[1],3)]=t
    if typ in('Cylinder','Torus') and abs(bb[2]-FLOOR)<1e-3 and abs(bb[5]-FLOOR-RR)<1e-3:refine.append(t)  # root fillets
    in_channel=bb[2]>RZ-CR-.01 and bb[5]<RZ+CR+.01
    if typ=='Cylinder' and in_channel and bb[0]<1e-6 and min(abs(bb[1]),abs(bb[4]))>H/2-CR-.1:refine.append(t)  # v5 grooves
assert len(sym)==1 and len(faces)==2*len(c['pockets']),(sym,faces)
for e in edges:e['face']=faces[round(e['face_y'],3)]
f=gmsh.model.mesh.field
f.add('Distance',1);f.setNumbers(1,'SurfacesList',sorted(set(refine)));f.setNumber(1,'Sampling',60)
f.add('Threshold',2);f.setNumber(2,'InField',1)
for k,v in dict(SizeMin=a.fine,SizeMax=a.coarse,DistMin=1,DistMax=10).items():f.setNumber(2,k,v)
for k,sy in((3,-1),(4,1)):  # fine boxes round the corner turns
    f.add('Box',k);y0,y1=sorted([sy*(BC[1]-3),sy*(BC[1]+BR+CR+2)])
    for kk,v in dict(VIn=a.fine,VOut=a.coarse,XMin=BC[0]-3,XMax=BC[0]+BR+CR+3,YMin=y0,YMax=y1,
                     ZMin=RZ-CR-3,ZMax=RZ+CR+3,Thickness=8).items():f.setNumber(k,kk,v)
f.add('Min',5);f.setNumbers(5,'FieldsList',[2,3,4]);f.setAsBackgroundMesh(5)
# Straight-sided quadratic tets: curved-edge ones invert on the R0.8 rounds,
# and at <=0.7 mm the faceting error on the R2 roots is ~0.03 mm.
for k,v in {'Mesh.MeshSizeMax':a.coarse,'Mesh.MeshSizeMin':.3,'Mesh.MeshSizeFromCurvature':6,
            'Mesh.MeshSizeExtendFromBoundary':0,'Mesh.Algorithm':6,'Mesh.Algorithm3D':10,
            'Mesh.ElementOrder':2,'Mesh.SecondOrderLinear':1,'General.NumThreads':os.cpu_count()}.items():
    gmsh.option.setNumber(k,v)
gmsh.model.mesh.generate(3)
tags,xyz,_=gmsh.model.mesh.getNodes()
idx=np.zeros(int(tags.max())+1,dtype=np.int64);idx[tags.astype(np.int64)]=np.arange(len(tags))
X=xyz.reshape(-1,3)
et,_,en=gmsh.model.mesh.getElements(3);assert list(et)==[11],et
# gmsh numbers the last two tet10 mid-edge nodes the other way round than C3D10.
tets=idx[en[0].astype(np.int64)].reshape(-1,10)[:,[0,1,2,3,4,5,6,7,9,8]]
assert np.allclose(X[tets[:,8]],(X[tets[:,1]]+X[tets[:,3]])/2,atol=1e-6)
def tris(t):
    et,_,en=gmsh.model.mesh.getElements(2,t);assert list(et)==[9],et
    return idx[en[0].astype(np.int64)].reshape(-1,6)
sym_tris=tris(sym[0])
SURF_T=np.concatenate([tris(t) for _,t in gmsh.model.getEntities(2)])
print(f'mesh: {len(X)} nodes, {len(tets)} C3D10, {3*len(X)} DOF, {time.time()-t0:.0f} s',flush=True)

# ---------------------------------------------------------------- infill
# Voxels one layer high. Each element takes the stiffness of its share of
# infill, sampled at its nodes and centroid, so the shell/infill boundary need
# not follow the mesh; elements entirely in infill report its stresses.
RHO=a.infill/100;LEVELS=8
VO=[(0,0),(1,1),(2,2),(0,1),(0,2),(1,2)]
def iso_C(E,nu):
    lam,mu=E*nu/(1+nu)/(1-2*nu),E/2/(1+nu);d=np.eye(3)
    return lam*np.einsum('ij,kl->ijkl',d,d)+mu*(np.einsum('ik,jl->ijkl',d,d)+np.einsum('il,jk->ijkl',d,d))
def plate(n,s=None):
    """Plane-stress plate of solid plastic in the plane of n and Z: its 3D
    stiffness, or with s (strain tensors) its in-plane stresses nn, zz, nz."""
    z=np.array([0,0,1.]);Ep,G=a.E/(1-a.nu**2),a.E/2/(1+a.nu)
    if s is not None:
        enn,ezz,enz=n@s@n,s[:,2,2],n@s@z
        return Ep*(enn+a.nu*ezz),Ep*(a.nu*enn+ezz),2*G*enz
    o=lambda *v:np.einsum('i,j,k,l->ijkl',*v);t=np.outer(n,z)+np.outer(z,n)
    return Ep*(o(n,n,n,n)+o(z,z,z,z)+a.nu*(o(n,n,z,z)+o(z,z,n,n)))+G*np.einsum('ij,kl->ijkl',t,t)
th=np.radians(a.infill_angle);GRID_N=[np.array([np.cos(th),np.sin(th),0]),np.array([-np.sin(th),np.cos(th),0])]
C_SOLID=iso_C(a.E,a.nu)
if a.infill_pattern=='gyroid':E_IN=a.E*RHO**a.infill_exponent;C_IN=iso_C(E_IN,a.nu)
else:C_IN=RHO/2*sum(plate(n) for n in GRID_N)+iso_C(a.E*(RHO/2)**3,a.nu)
S_IN=np.linalg.inv(np.array([[C_IN[i,j,k,l] for k,l in VO] for i,j in VO]))  # engineering shear strains
E_XYZ=1/np.diag(S_IN)[:3]
def in_plastic(S6):
    """Stresses in the infill's own plastic from its smeared ones (rows
    xx,yy,zz,xy,xz,yz): across layers, max and min principal."""
    if a.infill_pattern=='gyroid':
        ev=np.linalg.eigvalsh(tensors(S6,VO))*a.E/E_IN;return S6[:,2]*a.E/E_IN,ev[:,2],ev[:,0]
    e=S6@S_IN.T;e[:,3:]/=2;w=[plate(n,tensors(e,VO)) for n in GRID_N]
    p=[((nn+zz)/2+sg*np.hypot((nn-zz)/2,nz)) for nn,zz,nz in w for sg in(1,-1)]
    return np.max([zz for _,zz,_ in w],0),np.max(p+[0*p[0]],0),np.min(p+[0*p[0]],0)
IN_LABEL=f'x{a.E/E_IN:.0f}' if a.infill_pattern=='gyroid' else 'in its walls'
ANISO=[(0,0,0,0),(0,0,1,1),(1,1,1,1),(0,0,2,2),(1,1,2,2),(2,2,2,2),(0,0,0,1),(1,1,0,1),(2,2,0,1),(0,1,0,1),(0,0,0,2),
       (1,1,0,2),(2,2,0,2),(0,1,0,2),(0,2,0,2),(0,0,1,2),(1,1,1,2),(2,2,1,2),(0,1,1,2),(0,2,1,2),(1,2,1,2)]
def aniso(C):
    v=[f'{C[i]:.7g}' for i in ANISO];return '*ELASTIC,TYPE=ANISO\n'+'\n'.join(','.join(v[k:k+8]) for k in range(0,21,8))+'\n'
lev=np.zeros(len(tets),int)
if RHO<1:
    from scipy import ndimage
    t0=time.time();HV,DZ=.15,a.layer;GX0,GY0=0.,-H/2-2*HV
    NX,NY,NZ=int((W/2+2*HV)/HV)+1,int((H+4*HV)/HV)+1,int(np.ceil(X[:,2].max()/DZ))
    gx=GX0+(np.arange(NX)+.5)*HV+1.23e-5;gy=GY0+(np.arange(NY)+.5)*HV+2.34e-5;gz=(np.arange(NZ)+.5)*DZ
    # Vertical rays through the voxel columns: their surface crossings give the inside.
    P=X[SURF_T[:,:3]];e1=P[:,1,:2]-P[:,0,:2];e2=P[:,2,:2]-P[:,0,:2];det=e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0]
    k=np.abs(det)>1e-9;P,e1,e2,det=P[k],e1[k],e2[k],det[k]
    i0=np.ceil((P[:,:,0].min(1)-gx[0])/HV).astype(int).clip(0);i1=np.floor((P[:,:,0].max(1)-gx[0])/HV).astype(int).clip(None,NX-1)
    j0=np.ceil((P[:,:,1].min(1)-gy[0])/HV).astype(int).clip(0);j1=np.floor((P[:,:,1].max(1)-gy[0])/HV).astype(int).clip(None,NY-1)
    nj=(j1-j0+1).clip(0);n=(i1-i0+1).clip(0)*nj
    t=np.repeat(np.arange(len(P)),n);k=np.arange(n.sum())-np.repeat(np.cumsum(n)-n,n)
    ii=i0[t]+k//nj[t];jj=j0[t]+k%nj[t]
    d=np.c_[gx[ii],gy[jj]]-P[t,0,:2]
    u=(d[:,0]*e2[t,1]-d[:,1]*e2[t,0])/det[t];v=(e1[t,0]*d[:,1]-e1[t,1]*d[:,0])/det[t]
    hit=(u>=0)&(v>=0)&(u+v<=1);t,u,v=t[hit],u[hit],v[hit]
    z=P[t,0,2]+u*(P[t,1,2]-P[t,0,2])+v*(P[t,2,2]-P[t,0,2])
    cnt=np.zeros((NX*NY,NZ+1),np.int32);np.add.at(cnt,((ii*NY+jj)[hit],np.searchsorted(gz,z)),1)
    odd=cnt.sum(1)%2==1;assert odd.mean()<1e-3,f'{odd.sum()} voxel columns cross the surface an odd number of times'
    inside=(np.cumsum(cnt,1)[:,:NZ]%2==1)&~odd[:,None];inside=inside.reshape(NX,NY,NZ)
    full=np.concatenate([inside[::-1],inside])  # mirrored: the symmetry plane is no outline
    wall=np.zeros_like(inside)
    for k in range(NZ):wall[...,k]=ndimage.distance_transform_edt(full[...,k],sampling=HV)[NX:]-HV/2<a.walls
    up,dn=np.zeros(inside.shape,np.float32),np.zeros(inside.shape,np.float32);ru=rd=0
    for k in range(NZ):rd=np.where(inside[...,k],rd+DZ,0);dn[...,k]=rd
    for k in range(NZ-1,-1,-1):ru=np.where(inside[...,k],ru+DZ,0);up[...,k]=ru
    CORE=inside&~wall&(up-DZ/2>=a.top)&(dn-DZ/2>=a.bottom)
    def core_at(p):
        p=np.asarray(p);i=((np.abs(p[...,0])-GX0)/HV).astype(int).clip(0,NX-1)
        return CORE[i,((p[...,1]-GY0)/HV).astype(int).clip(0,NY-1),(p[...,2]/DZ).astype(int).clip(0,NZ-1)]
    frac=core_at(np.concatenate([X[tets],X[tets[:,:4]].mean(1,keepdims=True)],1)).mean(1)
    lev=np.rint(frac*LEVELS).astype(int)
    p=X[tets[:,:4]];vol=np.abs(np.einsum('ij,ij->i',p[:,1]-p[:,0],np.cross(p[:,2]-p[:,0],p[:,3]-p[:,0])))/6
    INFILL_SHARE=float((vol*frac).sum()/vol.sum())
    print(f'infill: {100*INFILL_SHARE:.0f}% of the volume, {(lev==LEVELS).sum()} elements all infill '
          f'({a.infill_pattern}, E x/y/z {"/".join(f"{v:.0f}" for v in E_XYZ)} MPa), {odd.sum()} odd voxel columns, {time.time()-t0:.0f} s',flush=True)

# ---------------------------------------------------------------- loads
def tri_geometry(T):
    p=X[T[:,:3]];n=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
    return p.mean(1),np.linalg.norm(n,axis=1)/2
def nodal(T,traction):
    """Consistent loads of a uniform traction on straight 6-node triangles:
    all of it on the three mid-side nodes."""
    F=np.zeros_like(X);_,A=tri_geometry(T)
    for k in(3,4,5):np.add.at(F,T[:,k],traction*(A/3)[:,None])
    return F
def bend_load(sy,theta0,theta1,u=(-1,0)):
    """Rope pressure on the wall of the corner turn on the sy side of y, for
    theta0..theta1, uniform along the turn. u is the pressing direction in the
    channel section as (radial, z): (-1,0) presses the inner wall towards the
    turn centre, (0,+-1) the roof/floor. Cosine across the wall within the
    contact angle. Triangles are picked by distance from the torus. Unscaled."""
    cen,_=tri_geometry(SURF_T)
    r=cen[:,:2]-BC*[1,sy];rho=np.linalg.norm(r,axis=1);rhat=r/rho[:,None]
    theta=np.degrees(np.arctan2(sy*r[:,1],r[:,0]))
    d=np.c_[rho-BR,cen[:,2]-RZ];dn=np.linalg.norm(d,axis=1);d/=dn[:,None]
    psi=np.degrees(np.arccos(np.clip(d@np.array(u,float),-1,1)))
    on=(np.abs(dn-CR)<.08)&(theta>=theta0)&(theta<=theta1)&(psi<a.contact_angle)
    p=np.where(on,np.cos(np.radians(psi)*90/a.contact_angle),0)
    m=p>0;assert m.any(),('no rope contact surface found',sy,theta0,theta1,u)
    return nodal(SURF_T[m],(u[0]*np.c_[rhat[m],np.zeros(m.sum())]+u[1]*np.array([0,0,1.]))*p[m,None])
def scaled(F,R):
    return F*R/np.linalg.norm(F.sum(0)[:2])
def wrap_load(sy,wrap):
    """In-plane rope pressure of a turn by wrap deg for a rope tension of 1 N.
    Beyond WALL_END the rest of the turn bears on the edge of the round."""
    tw=min(wrap,WALL_END)
    F=scaled(bend_load(sy,0,tw),2*np.sin(np.radians(tw)/2))
    if wrap>WALL_END+1e-6:
        F=F+scaled(bend_load(sy,WALL_END-KINK_SPREAD,WALL_END),2*np.sin(np.radians(wrap-WALL_END)/2))
    return F
phi=a.strand_angle;Tn=a.force/(2*np.cos(np.radians(phi)))
cases=[]
for e in edges:
    T=tris(e['face']);cen,A=tri_geometry(T)
    on=cen[:,0]<=a.finger_width/2
    e['finger_area']=2*A[on].sum()
    Ff=nodal(T,np.c_[0*A,np.where(on,e['push'],0),0*A])
    Ff*=a.force/2/abs(Ff[:,1].sum())
    far,exit_=e['push'],-e['push']
    Fr=Tn*(wrap_load(far,90)+wrap_load(exit_,phi))
    e['rope_balance_error']=float(abs(Fr[:,1].sum()/Ff[:,1].sum()+1))
    Fr*=-Ff[:,1].sum()/Fr[:,1].sum()  # exact balance along Y
    # The finger load sits above the rope plane. The hanging board tilts until
    # the hand pulls along the line through the anchor, so the fingers also pull
    # slightly out of plane (through pad friction) and the tilted strands press
    # the floor or roof of the exit-side tunnels. Size that pair to cancel the
    # moment; the sign picks floor or roof.
    Gf=nodal(T,np.c_[0*A,0*A,np.where(on,1.,0)]);Gf/=Gf[:,2].sum()
    Mx=lambda F:(X[:,1]*F[:,2]-X[:,2]*F[:,1]).sum()
    for sz in(-1,1):
        Ge=bend_load(exit_,0,WALL_END,(0,sz));Ge/=abs(Ge[:,2].sum())
        Fz=-Mx(Ff+Fr)/Mx(Ge-sz*Gf)
        if Fz>=0:break
    F=Ff+Fr+Fz*(Ge-sz*Gf)
    assert np.isfinite(F).all() and abs(F[:,1].sum())<1e-6*a.force and abs(F[:,2].sum())<1e-6*a.force and abs(Mx(F))<1e-6*a.force
    e['finger_pull_out_N']=-2*sz*Fz
    cases.append(F)

# ---------------------------------------------------------------- CalculiX
# The loads balance in Y, Z and about X, so besides the symmetry plane the
# board only needs rigid-body supports: Y at one node, Z at two nodes of the
# back face. Their reactions are round-off and are reported as a check.
n_sym=np.unique(sym_tris)
near=lambda q:n_sym[np.argmin(np.linalg.norm(X[n_sym]-q,axis=1))]
n_y=near([0,0,0]);n_z=np.array([near([0,-H/2+15,0]),near([0,H/2-15,0])])
def nset(name,ids,kw='NSET'):
    ids=ids+1;return f'*{kw},{kw}={name}\n'+'\n'.join(','.join(map(str,ids[i:i+16])) for i in range(0,len(ids),16))+'\n'
with open(work/'hangboard.inp','w') as fh:
    fh.write('*HEADING\nHangboard edge load cases\n*NODE\n')
    np.savetxt(fh,np.c_[np.arange(1,len(X)+1),X],fmt=['%d','%.6f','%.6f','%.6f'],delimiter=',')
    fh.write('*ELEMENT,TYPE=C3D10,ELSET=EALL\n')
    np.savetxt(fh,np.c_[np.arange(1,len(tets)+1),tets+1],fmt='%d',delimiter=',')
    fh.write(nset('NSYM',n_sym)+nset('NZ',n_z)+nset('NY',np.array([n_y])))
    if RHO<1:
        for l in np.unique(lev):
            fh.write(nset(f'M{l}',np.where(lev==l)[0],'ELSET')+f'*MATERIAL,NAME=M{l}\n'+aniso(C_SOLID+(C_IN-C_SOLID)*l/LEVELS)+
                     f'*SOLID SECTION,ELSET=M{l},MATERIAL=M{l}\n')
    else:fh.write(f'*MATERIAL,NAME=PRINT\n*ELASTIC\n{a.E},{a.nu}\n*SOLID SECTION,ELSET=EALL,MATERIAL=PRINT\n')
    for e,F in zip(edges,cases):
        fh.write(f'** edge {e["depth"]} mm\n*STEP\n*STATIC\n*BOUNDARY\nNSYM,1,1\nNZ,3,3\nNY,2,2\n*CLOAD,OP=NEW\n')
        nz=np.where(np.abs(F).sum(1)>0)[0]
        for d in range(3):
            m=nz[F[nz,d]!=0];np.savetxt(fh,np.c_[m+1,np.full(len(m),d+1),F[m,d]],fmt=['%d','%d','%.8e'],delimiter=',')
        fh.write('*NODE FILE\nU\n*EL FILE\nS\n')
        for s in('NSYM','NZ','NY'):fh.write(f'*NODE PRINT,NSET={s},TOTALS=ONLY\nRF\n')
        if (lev==LEVELS).any():fh.write(f'*EL PRINT,ELSET=M{LEVELS}\nS\n')
        fh.write('*END STEP\n')
gmsh.finalize()
ccx=os.environ.get('CCX') or shutil.which('ccx') or subprocess.run(['mise','-C',str(here),'which','ccx'],capture_output=True,text=True).stdout.strip()
assert ccx,'ccx not found: run `mise install` in the repository'
env=dict(os.environ,OMP_NUM_THREADS=str(os.cpu_count()),CCX_NPROC_EQUATION_SOLVER=str(os.cpu_count()))
t0=time.time();print(f'solving {len(edges)} load cases with {ccx}',flush=True)
with open(work/'ccx.log','w') as log:
    r=subprocess.run([ccx,'-i','hangboard'],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0 and 'ERROR' not in (work/'ccx.log').read_text(),f'ccx failed, see {work/"ccx.log"}'
print(f'solved in {time.time()-t0:.0f} s',flush=True)

# ---------------------------------------------------------------- results
def read_frd(path,n):
    """Nodal result blocks of a CalculiX .frd file, in order: [(name, array)]."""
    out=[];cur=None
    with open(path) as fh:
        for line in fh:
            if line.startswith(' -4'):name=line[5:13].strip();cur=[];k=0
            elif cur is not None and line.startswith(' -5'):k+=line[5:13].strip()!='ALL'
            elif cur is not None and line.startswith(' -1'):cur.append(line)
            elif cur is not None and line.startswith(' -3'):
                v=np.zeros((n,k))
                for l in cur:v[int(l[3:13])-1]=[float(l[13+12*j:25+12*j]) for j in range(v.shape[1])]
                out.append((name,v));cur=None
    return out
blocks=read_frd(work/'hangboard.frd',len(X))
disp=[v for nm,v in blocks if nm=='DISP'];stress=[v for nm,v in blocks if nm=='STRESS']
assert len(disp)==len(stress)==len(edges)
dat=(work/'hangboard.dat').read_text()
reac=[(m.group(1),[float(m.group(i)) for i in(2,3,4)]) for m in re.finditer(r'total force \(fx,fy,fz\) for set (\w+).*\n\s*\n\s*(\S+)\s+(\S+)\s+(\S+)',dat)]
# Integration-point stresses of the all-infill elements: (element, S tensor) per case.
core_s,cur=[],None
for l in dat.splitlines() if (lev==LEVELS).any() else []:
    if 'stresses (elem' in l:cur=[];core_s.append(cur)
    elif 'for set' in l:cur=None
    elif cur is not None and len(l.split())==8:cur.append(l.split())  # skips the next step's banner
assert not core_s or len(core_s)==len(edges)
def tensors(S6,ij):
    s=np.zeros((len(S6),3,3))
    for k,(i,j) in enumerate(ij):s[:,i,j]=s[:,j,i]=S6[:,k]
    return s
XC=X[tets[:,:4]].mean(1)

def where(i):return [round(float(v),1) for v in X[i]]
def peak(v,mask,sign=1):
    i=np.where(mask)[0][np.argmax(sign*v[mask])];return dict(MPa=round(float(v[i]),2),at_mm=where(i))
summary=dict(model=dict(step=str(a.step),wall_end_deg=round(WALL_END,1),
    kink_force_per_T=round(2*np.sin(np.radians(max(0,90-WALL_END))/2),3),step_sha1=hashlib.sha1(a.step.read_bytes()).hexdigest(),nodes=len(X),elements=len(tets),force_N=a.force,
    strand_angle_deg=phi,strand_tension_N=round(Tn,1),finger_width_mm=a.finger_width,
    rope_contact_half_angle_deg=a.contact_angle,E_MPa=a.E,nu=a.nu,
    note='S33 = tension across print layers (Z). Linear-elastic; layer bonding is not modelled. '+
         ('Perimeters and top/bottom solid are solid plastic, sparse infill a homogeneous solid of reduced stiffness; '
          'peaks outside "infill" are nodal values, in "infill" integration-point values of elements entirely in infill, '
          'with equivalent_MPa the stress in the infill\'s own plastic (gyroid: MPa*E/E_infill; grid: in its walls).'
          if RHO<1 else 'Homogeneous solid: 100% infill.')),cases=[])
if RHO<1:summary['model']['infill']=dict(pattern=a.infill_pattern,density_pct=a.infill,
    **(dict(stiffness_exponent=a.infill_exponent) if a.infill_pattern=='gyroid' else dict(wall_angle_deg=a.infill_angle)),
    E_xyz_MPa=[round(float(v),1) for v in E_XYZ],
    walls_mm=a.walls,top_mm=a.top,bottom_mm=a.bottom,layer_mm=a.layer,volume_share=round(INFILL_SHARE,3))
def corner(sy,P=X):
    """Points within 5 mm of the rope tube of the corner turn on the sy side."""
    r=P[:,:2]-BC*[1,sy];th=np.degrees(np.arctan2(sy*r[:,1],r[:,0]))
    dn=np.hypot(np.linalg.norm(r,axis=1)-BR,P[:,2]-RZ)
    return (dn<CR+5)&(th>-15)&(th<105)
def bar_of(e,P=X):
    """The loaded bar with its root fillets, through the floor; stops short of the bends."""
    y0,y1=e['bar'];return (P[:,1]>=y0-RR-.5)&(P[:,1]<=y1+RR+.5)&(P[:,0]<=BC[0]-1)
def floor_of(P=X):
    """Floor plate under the pockets, at least 4 mm from the edge roots."""
    return (P[:,2]<FLOOR-1)&(P[:,0]<PW/2-7)&np.any([np.abs(P[:,1]-yc)<PH/2-4 for yc,_,_ in c['pockets']],axis=0)
for ci,(e,U,S) in enumerate(zip(edges,disp,stress)):
    s=tensors(S,[(0,0),(1,1),(2,2),(0,1),(1,2),(2,0)])
    ev=np.linalg.eigvalsh(s);s1,s3,szz=ev[:,2],ev[:,0],S[:,2]
    vm=np.sqrt(((ev[:,0]-ev[:,1])**2+(ev[:,1]-ev[:,2])**2+(ev[:,2]-ev[:,0])**2)/2)
    bar=bar_of(e);far,ext=corner(e['push']),corner(-e['push']);floor=floor_of()
    allm=np.ones(len(X),bool)
    e.update(s1=s1,s3=s3,szz=szz)
    infill={}
    if core_s:
        b=np.array(core_s[ci],float);P=XC[b[:,0].astype(int)-1]
        ev=np.linalg.eigvalsh(tensors(b[:,2:],VO));pl=in_plastic(b[:,2:])
        def cpeak(v,vp,m,sign=1):
            if not m.any():return None
            i=np.where(m)[0][np.argmax(sign*vp[m])]
            return dict(MPa=round(float(v[i]),3),equivalent_MPa=round(float(vp[i]),2),at_mm=[round(float(q),1) for q in P[i]])
        for nm,m in dict(loaded_bar=bar_of(e,P),far_bends=corner(e['push'],P),exit_bends=corner(-e['push'],P),
                         floor=floor_of(P),whole_part=np.ones(len(P),bool)).items():
            infill[nm]=dict(S33_max=cpeak(b[:,4],pl[0],m),S1_max=cpeak(ev[:,2],pl[1],m),S3_min=cpeak(ev[:,0],pl[2],m,-1))
        e['infill_s33_eq']=infill['whole_part']['S33_max']['equivalent_MPa']
    summary['cases'].append(dict(edge_mm=e['depth'],face_y_mm=e['face_y'],rope_balance_error=round(e['rope_balance_error'],4),
        finger_pull_out_N=round(e['finger_pull_out_N'],1),
        push='-Y' if e['push']<0 else '+Y',finger_pressure_MPa=round(a.force/e['finger_area'],3),
        loaded_bar=dict(S33_max=peak(szz,bar),S1_max=peak(s1,bar)),
        far_bends=dict(S1_max=peak(s1,far),S3_min=peak(s3,far,-1),S33_max=peak(szz,far)),
        exit_bends=dict(S1_max=peak(s1,ext),S3_min=peak(s3,ext,-1),S33_max=peak(szz,ext)),
        floor=dict(S1_max=peak(s1,floor),S3_min=peak(s3,floor,-1),S33_max=peak(szz,floor)),
        whole_part=dict(S33_max=peak(szz,allm),S1_max=peak(s1,allm),S3_min=peak(s3,allm,-1),
                        von_mises_max=peak(vm,allm),displacement_max_mm=round(float(np.linalg.norm(U,axis=1).max()),4)),
        **(dict(infill=infill) if infill else {})))
summary['reactions_N']=[{'edge_mm':e['depth'],**{nm:[round(v,2) for v in f] for nm,f in reac[3*i:3*i+3]}} for i,e in enumerate(edges)]
(a.out/'fea.json').write_text(json.dumps(summary,indent=2))

# ---------------------------------------------------------------- figures
SURF,INK,INK2,MUTED='#fcfcfb','#0b0b0b','#52514e','#898781'
DIV=LinearSegmentedColormap.from_list('div',['#0d366b','#2a78d6','#86b6ef','#f0efec','#f2a19e','#e34948','#7a1514'])
RED=LinearSegmentedColormap.from_list('red',['#f7efed','#f2a19e','#e34948','#a52423','#5e0f0e'])
BLUE=LinearSegmentedColormap.from_list('blue',['#eef3fa','#9ec5f4','#3987e5','#1c5cab','#0d366b'])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'text.color':INK,'axes.labelcolor':INK2,
    'xtick.color':MUTED,'ytick.color':MUTED,'axes.edgecolor':MUTED,'figure.facecolor':SURF,'axes.facecolor':SURF})
ROPE_D=a.rope_diameter
# x=0 face of the half model: the section through the middle of the pockets.
q=sym_tris;sub=np.r_[q[:,[0,3,5]],q[:,[3,1,4]],q[:,[5,4,2]],q[:,[3,4,5]]]
def section(o,n,eu,ev,vals,mirror=False,urange=(-np.inf,np.inf)):
    """Section of the corner nodes' linear field with the plane through o with
    normal n, in plane coordinates (u, v) along eu, ev."""
    P=X[tets[:,:4]]-o;V=np.stack(vals,-1)[tets[:,:4]];s=P@n;uc=P.mean(1)@eu
    m=(s.min(1)<0)&(s.max(1)>0)&(uc>urange[0])&(uc<urange[1]);P,V,s=P[m],V[m],s[m]
    pts,vv,ok=[],[],[]
    for i,j in[(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]:
        cut=(s[:,i]<0)!=(s[:,j]<0);t=np.where(cut,s[:,i]/(s[:,i]-s[:,j]+1e-30),0)[:,None]
        pts.append(P[:,i]+(P[:,j]-P[:,i])*t);vv.append(V[:,i]+(V[:,j]-V[:,i])*t);ok.append(cut)
    pts,vv,ok=np.stack(pts,1),np.stack(vv,1),np.stack(ok,1)
    pts=np.stack([pts@eu,pts@ev],-1)
    cen=(pts*ok[...,None]).sum(1)/ok.sum(1)[:,None]
    ang=np.where(ok,np.arctan2(pts[...,1]-cen[:,None,1],pts[...,0]-cen[:,None,0]),np.inf)
    o_=np.argsort(ang,1);pts=np.take_along_axis(pts,o_[...,None],1);vv=np.take_along_axis(vv,o_[...,None],1)
    quad=ok.sum(1)==4
    tri_p=np.r_[pts[:,[0,1,2]],pts[quad][:,[0,2,3]]];tri_v=np.r_[vv[:,[0,1,2]],vv[quad][:,[0,2,3]]]
    if mirror:tri_p=np.r_[tri_p,tri_p*[-1,1]];tri_v=np.r_[tri_v,tri_v]  # the full board
    return Triangulation(tri_p[...,0].ravel(),tri_p[...,1].ravel(),np.arange(tri_p.shape[0]*3).reshape(-1,3)),tri_v.reshape(-1,tri_v.shape[-1])
def mark(ax,x,y,v,txt,left=False):
    ax.plot(x,y,'o',ms=9,mfc='none',mec=INK,mew=1.5)
    ax.annotate(f'{txt} {v:.1f} MPa',(x,y),(-8 if left else 8,8),textcoords='offset points',fontsize=8,color=INK,ha='right' if left else 'left')
def infill_outline(ax,o,eu,ev,ur,vr):
    """Dashed outline of the sparse infill in the plane o + u*eu + v*ev."""
    if RHO>=1:return
    U,V=np.meshgrid(np.arange(*ur,.1),np.arange(*vr,.1));p=o+U[...,None]*eu+V[...,None]*ev
    ax.contour(U,V,core_at(p).astype(float),[.5],colors=INK2,linewidths=.7,linestyles='--')
def style(ax,title,xl,yl=None):
    ax.set_aspect('equal');ax.set_title(title,fontsize=10,color=INK);ax.set_xlabel(xl)
    if yl:ax.set_ylabel(yl)
def bar_ends(v,p=99.7):return max(float(np.percentile(np.abs(v),p)),1e-6)
S33_LABEL='S33, MPa  (+ = layers pulled apart)'
for e,case in zip(edges,summary['cases']):
    fig=plt.figure(figsize=(16,11.5))
    gs=fig.add_gridspec(2,3,width_ratios=[.5,1,1],height_ratios=[1.25,1],left=.05,right=.97,top=.9,bottom=.06,wspace=.25,hspace=.28)
    ax=fig.add_subplot(gs[:,0]);v=e['szz'];lim=bar_ends(v[np.unique(sub)])
    tc=ax.tripcolor(X[:,2],X[:,1],sub,v,cmap=DIV,norm=TwoSlopeNorm(0,-lim,lim),shading='gouraud')
    fig.colorbar(tc,ax=ax,shrink=.7,pad=.02,extend='both').set_label(S33_LABEL)
    i=n_sym[np.argmax(v[n_sym])];mark(ax,X[i,2],X[i,1],v[i],'max')
    zf=FLOOR+e['depth']*.75;ax.annotate('',(zf,e['face_y']+e['push']*.5),(zf,e['face_y']-e['push']*14),
        arrowprops=dict(arrowstyle='-|>',color=INK,lw=1.5));ax.text(zf+1.5,e['face_y']-e['push']*10,'fingers',fontsize=8,color=INK)
    infill_outline(ax,np.array([.01,0,0]),np.array([0,0,1.]),np.array([0,1.,0]),(0,max(X[:,2])+.5),(-H/2-1,H/2+1))
    style(ax,'Pocket-centre section\ntension across layers','Z (thickness), mm','Y, mm')
    ZS=RZ-.5  # just under the rope axis: open rope seats start at the axis
    tri,vals=section(np.array([0,0,ZS]),np.array([0,0,1.]),np.array([1.,0,0]),np.array([0,1.,0]),[e['s1'],-e['s3']],mirror=True)
    for ax,k,cmap,lab,title,sgn in[(fig.add_subplot(gs[0,1]),0,RED,'max principal S1, MPa','In-plane tension',1),
                                  (fig.add_subplot(gs[0,2]),1,BLUE,'|min principal S3|, MPa','Compression (rope bearing)',-1)]:
        vv=vals[:,k];vmax=float(np.percentile(vv,99.9))
        tc=ax.tripcolor(tri,np.clip(vv,0,None),cmap=cmap,norm=Normalize(0,vmax),shading='gouraud')
        fig.colorbar(tc,ax=ax,shrink=.85,pad=.02,extend='max').set_label(lab)
        j=np.argmax(vv);mark(ax,tri.x[j],tri.y[j],sgn*vv[j],'peak',left=tri.x[j]>0)
        for sy,wrap in[(e['push'],90),(-e['push'],phi)]:
            for sx in(-1,1):
                tb=np.radians(wrap/2)  # resultant along the bisector of the wrap
                c0=BC*[sx,sy];d=-np.array([sx*np.cos(tb),sy*np.sin(tb)]);p0=c0-d*(BR+CR+6)
                ax.annotate('',c0-d*(BR-CR-1),p0,arrowprops=dict(arrowstyle='-|>',color=INK,lw=1.2))
            ax.text(0,sy*(H/2+6),f'rope, {wrap:.0f}° wrap',ha='center',va='center',fontsize=8,color=INK2)
        infill_outline(ax,np.array([0,0,ZS]),np.array([1.,0,0]),np.array([0,1.,0]),(-W/2-1,W/2+1),(-H/2-1,H/2+1))
        ax.set_xlim(-W/2-12,W/2+12);ax.set_ylim(-H/2-12,H/2+12)
        style(ax,f'{title}\nsection at the rope plane, Z={ZS:g} mm','X, mm')
    # Cuts across the rope channel, through the bend axis, mid-way along each wrap.
    for col,(sy,wrap,name) in enumerate([(e['push'],90,'sling-side'),(-e['push'],phi,'anchor-side')]):
        ax=fig.add_subplot(gs[1,col+1]);tb=np.radians(wrap/2)
        r=np.array([np.cos(tb),sy*np.sin(tb),0]);o=np.array([BC[0],sy*BC[1],0])
        tri,vals=section(o,np.cross(r,[0,0,1]),r,np.array([0,0,1.]),[e['szz']],urange=(-14,BR+CR+12))
        vv=vals[:,0];lim=float(np.percentile(vv[vv>0],99.9))  # scaled to the tension; bearing compression clips
        tc=ax.tripcolor(tri,vv,cmap=DIV,norm=TwoSlopeNorm(0,-lim,lim),shading='gouraud')
        fig.colorbar(tc,ax=ax,shrink=.85,pad=.02,extend='both').set_label(S33_LABEL)
        rc=BR-CR+ROPE_D/2  # cord pressed against the inner wall
        j=np.argmax(vv);mark(ax,tri.x[j],tri.y[j],vv[j],'max',left=tri.x[j]<rc)
        ax.add_patch(plt.Circle((rc,RZ),ROPE_D/2,fill=False,ls='--',lw=1,ec=INK2))
        ax.annotate('',(BR-CR-.3,RZ),(rc+ROPE_D/2-.6,RZ),arrowprops=dict(arrowstyle='-|>',color=INK,lw=1.2))
        ax.text(rc,RZ-ROPE_D/2-2.2,'rope',ha='center',fontsize=8,color=INK2)
        infill_outline(ax,o,r,np.array([0,0,1.]),(-14,BR+CR+12),(-1,max(X[:,2])+1))
        ax.set_xlim(-14,BR+CR+12);ax.set_ylim(-1,max(X[:,2])+1)
        style(ax,f'Across the {name} rope channel ({wrap:.0f}° wrap),\nmid-bend: tension across layers',
              'distance from the bend axis, mm','Z, mm')
    fig.suptitle(f'{e["depth"]} mm edge  -  {a.force:.0f} N finger load ({a.force/9.81:.0f} kg), '
                 f'rope strands {phi:.0f}° from vertical, T = {Tn:.0f} N per strand',fontsize=13,color=INK)
    fig.text(.5,.012,('Linear-elastic, homogeneous solid. ' if RHO>=1 else
             f'Dashed: outline of the {a.infill:g}% infill ({a.walls:g} mm walls, {a.top:g}/{a.bottom:g} mm top/bottom), '
             f'{a.infill_pattern}, drawn at its smeared stress. ')+
             'Peaks are nodal values; colour scales clip at the 99.7th/99.9th percentile. '
             'Rope as frictionless pressure on the bend inner walls.',ha='center',fontsize=8,color=MUTED)
    fig.savefig(a.out/f'edge_{e["depth"]}.png',dpi=120);plt.close(fig)
# Summary: the same measure (S33) at the two candidate failure sites, then bearing.
labels=[f'{s["edge_mm"]} mm' for s in summary['cases']]
edge_s33=[s['loaded_bar']['S33_max']['MPa'] for s in summary['cases']]
rope_s33=[max(s['far_bends']['S33_max']['MPa'],s['exit_bends']['S33_max']['MPa']) for s in summary['cases']]
bearing=[-min(s['far_bends']['S3_min']['MPa'],s['exit_bends']['S3_min']['MPa']) for s in summary['cases']]
C1,C2='#2a78d6','#eb6834'
fig,axs=plt.subplots(1,2,figsize=(12,4.2),sharey=True,gridspec_kw={'width_ratios':[1.3,1]})
yy=np.arange(len(labels))
def bars(ax,y,vals,col,lab=None,h=.34):
    ax.barh(y,vals,height=h,color=col,label=lab,edgecolor=SURF,linewidth=1)
    for y_,v_ in zip(y,vals):ax.text(v_,y_,f' {v_:.1f}',va='center',fontsize=8.5,color=INK)
series=[(edge_s33,C1,'edge root'),(rope_s33,C2,'rope corners')]
if core_s:series.append(([e['infill_s33_eq'] for e in edges],'#8a5cd1',f'{a.infill_pattern} infill, {IN_LABEL}'))
h=.68/len(series)
for k,(vals,col,lab) in enumerate(series):bars(axs[0],yy+(k-(len(series)-1)/2)*h,vals,col,lab,h)
axs[0].legend(frameon=False,loc='lower right',bbox_to_anchor=(1,1),ncol=len(series),fontsize=9,labelcolor=INK2)
axs[0].set_title('Tension across layers (S33) - where it peaks',fontsize=10,color=INK,loc='left')
bars(axs[1],yy,bearing,C2);axs[1].set_title('Rope bearing compression on the bend wall (|S3|)',fontsize=10,color=INK,loc='left')
for ax,vals in zip(axs,(sum((v for v,_,_ in series),[]),bearing)):
    ax.set_xlabel('MPa');ax.set_xlim(0,max(vals)*1.2)
    ax.grid(axis='x',color='#e6e5e1',lw=.8);ax.set_axisbelow(True)
    for sp in('top','right','left'):ax.spines[sp].set_visible(False)
    ax.tick_params(axis='y',length=0)
axs[0].set_yticks(yy,labels);axs[0].invert_yaxis()
fig.suptitle(f'Peak stress per edge at {a.force:.0f} N ({a.force/9.81:.0f} kg) - stresses scale linearly with load',fontsize=11,color=INK,x=.02,ha='left')
fig.subplots_adjust(left=.07,right=.98,top=.8,bottom=.13,wspace=.15)
fig.savefig(a.out/'summary.png',dpi=130);plt.close(fig)
print(f'wrote {a.out}/fea.json, summary.png, edge_*.png; CalculiX files in {work}')
