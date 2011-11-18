from pysb import *

# pySB adaptation of
# Model-based dissection of CD95 signaling dynamics reveals both a pro- and antiapoptotic role of c-FLIPL.
# Fricker N, Beaudouin J, Richter P, Eils R, Krammer PH, Lavrik IN. J Cell Biol. 2010 Aug 9;190(3):377-89.
# PMID: 20696707 
#
# by Jeremie Roux, Will Chen


Model()

transloc = .01; # rate of translocation between the cytosolic and mitochondrial compartments

v = .07; # mitochondria compartment volume/cell volume

# Non-zero initial conditions (in molecules per cell):
Parameter('L_0'        , 1500e3); # baseline level of ligand for most experiments (corresponding to 50 ng/ml SuperKiller TRAIL)
Parameter('pR_0'       , 170.999e3);  # TRAIL receptor (for experiments not involving siRNA)
Parameter('FADD_0'     , 133.165e3);
Parameter('flipL_0'    , 0.49995e3);  # FlipL 1X = 0.49995e3
Parameter('flipS_0'    , 0.422e3);  # Flip
Parameter('pC8_0'      , 200.168e3);  # procaspase-8 (pro-C8)
Parameter('Bid_0'       , 100e3);  # Bid

Monomer('L', ['b'])
Monomer('pR', ['b', 'rf'])
Monomer('FADD', ['rf', 'fe'])
Monomer('flipL', ['b', 'fe', 'ee', 'D384'],
        {'D384': ['U','C']}
        )
Monomer('flipS', ['b', 'fe', 'ee'])
Monomer('pC8', ['fe', 'ee', 'D384', 'D400'],
        {'D384': ['U','C'],
	 'D400': ['U','C']}
        )
Monomer('Bid') #called Apoptosis substrat in Lavrik's model
Monomer('tBid')

flip_monomers = (flipL, flipS);

# L + R <--> L:R
Parameter('kf1', 70.98e-03) #70.98e-03
Parameter('kr1', 0)
Rule('R_L_Binding', L (b=None) + pR (b=None, rf=None) >> L (b=1) % pR (b=1, rf=None), kf1)

# FADD binds
Parameter('kf29', 84.4211e-03) #84.4211e-03
Parameter('kr29', 0)
Rule('RL_FADD_Binding', pR (b=ANY, rf=None) + FADD (rf=None, fe=None) >> pR (b=ANY, rf=2) % FADD (rf=2, fe=None), kf29,kr29)

#C8 binds to L:R:FADD
Parameter('kf30', 3.19838e-03) #3.19838e-03
Parameter('kr30', 0.1) #0.1
Rule('RLFADD_C8_Binding', FADD (rf=ANY, fe=None) + pC8 (fe=None, ee=None, D384='U') <> FADD (rf=ANY, fe=1) % pC8 (fe=1, ee=None, D384='U'), kf30, kr30)

#FLIP(variants) bind to L:R:FADD
Parameter('kf31', 69.3329e-03)
Parameter('kr31', 0.0)
Parameter('kf32', 69.4022e-03)
Parameter('kr32', 0.08)
# FIXME: this pattern requires a dummy kr31 which is ultimately ignored
for flip_m, kf, kr, reversible in (zip(flip_monomers, (kf31,kf32), (kr31,kr32), (False,True))):
    rule = Rule('RLFADD_%s_Binding' % flip_m.name, FADD (rf=ANY, fe=None) + flip_m (fe=None, ee=None) <> FADD (rf=ANY, fe=1) % flip_m (fe=1, ee=None), kf, kr)
    if reversible is False:
        rule.is_reversible = False;
        rule.rate_reverse = None;

pC8_HomoD   = pC8 (fe=ANY, ee=1, D384='U') % pC8   (fe=ANY, ee=1, D384='U')
pC8_HeteroD = pC8 (fe=ANY, ee=1, D384='U') % flipL (fe=ANY, ee=1, D384='U')
p43_HomoD   = pC8 (fe=ANY, ee=1, D384='C') % pC8   (fe=ANY, ee=1, D384='C')
p43_HeteroD = pC8 (fe=ANY, ee=1, D384='C') % flipL (fe=ANY, ee=1, D384='C')

#L:R:FADD:C8 dimerizes
Parameter('kf33', 2.37162)
Parameter('kr33', 0.1)
Parameter('kc33', 1e-05)
Rule('RLFADD_C8_C8_Binding', pC8 (fe=ANY, ee=None, D384='U') + pC8 (fe=ANY, ee=None, D384='U') <> pC8_HomoD, kf33, kr33)

#L:R:FADD:C8 L:R:FADD:FLIP(variants) dimerizes
Parameter('kf34', 4.83692)
Parameter('kr34', 0)
Parameter('kf35', 2.88545)
Parameter('kr35', 1)
# FIXME: this pattern requires a dummy kr31 which is ultimately ignored
for flip_m, kf, kr, reversible in (zip(flip_monomers, (kf34,kf35), (kr34,kr35), (False,True))):
    rule = Rule('RLFADD_C8_%s_Binding' % flip_m.name, pC8 (fe=ANY, ee=None, D384='U') + flip_m (fe=ANY, ee=None) <> pC8 (fe=ANY, ee=1, D384='U') % flip_m (fe=ANY, ee=1), kf, kr)
    if reversible is False:
        rule.is_reversible = False;
        rule.rate_reverse = None;

Parameter('kc36', 0.223046e-3)
#Homodimer catalyses Homodimer ?: no p18 is released. Only this "cleaved" p43 homoD is the product that will transform into a p18 + L:R:FADD in later reaction.
Rule('HomoD_cat_HomoD', pC8_HomoD + pC8_HomoD >> pC8_HomoD + p43_HomoD, kc36)
#Homodimer catalyses Heterodimer ?????
Rule('HomoD_cat_HeteroD', pC8_HomoD + pC8_HeteroD >> pC8_HomoD + p43_HeteroD, kc36)

Parameter('kc37', 0.805817e-3)
#Heterodimer catalyses Heterodimer ?????
Rule('HeteroD_cat_HeteroD', pC8_HeteroD + pC8_HeteroD >> pC8_HeteroD + p43_HeteroD, kc37)
#Heterodimer catalyses Homodimer ?????
Rule('HeteroD_cat_HomoD', pC8_HeteroD + pC8_HomoD >> pC8_HeteroD + p43_HomoD, kc37)

Parameter('kc38', 1.4888e-3)
#Cleaved Homodimer catalyses Homodimer ?????
Rule('Cl_HomoD_cat_HomoD', p43_HomoD + pC8_HomoD >> p43_HomoD + p43_HomoD, kc38)
#Cleaved HomoD catalyses Heterodimer ?????
Rule('Cl_HomoD_cat_HeteroD', p43_HomoD + pC8_HeteroD >> p43_HomoD + p43_HeteroD, kc38)

Parameter('kc39', 13.098e-3)
#Cleaved HeteroD catalyses Homodimer ?????
Rule('Cl_heteroD_cat_HomoD', p43_HeteroD + pC8_HomoD >> p43_HeteroD + p43_HomoD, kc39)
#Cleaved HeteroD catalyses Heterodimer ?????
Rule('Cl_heteroD_cat_HeteroD', p43_HeteroD + pC8_HeteroD >> p43_HeteroD + p43_HeteroD, kc39)

#Cleaved HomoD catalyses Cleaved HomoD to p18 and release L:R:FADD
Parameter('kc40', 0.999273e-3)
Rule('Cl_HomoD_cat_Cl_HomoD', pC8 (fe=ANY, ee=1, D384='C', D400='U') % pC8 (fe=ANY, ee=1, D384='C', D400='U') +
     FADD (rf=ANY, fe=2) % pC8 (fe=2, ee=3, D384='C', D400='U') % FADD (rf=ANY, fe=4) % pC8 (fe=4, ee=3, D384='C', D400='U') >>
     pC8 (fe=ANY, ee=1, D384='C', D400='U') % pC8 (fe=ANY, ee=1, D384='C', D400='U') +
     FADD (rf=ANY, fe=None) + FADD (rf=ANY, fe=None) + pC8 (fe=None, ee=1, D384='C',D400='C') % pC8 (fe=None, ee=1, D384='C',D400='C'), 
     kc40)

#Cleaved HeteroD catalyses Cleaved HomoD to p18 and release L:R:FADD
Parameter('kc41', 0.982109e-3)
Rule('Cl_HeteroD_cat_Cl_HomoD', pC8 (fe=ANY, ee=1, D384='C', D400='U') % flipL (fe=ANY, ee=1, D384='C') +
     FADD (rf=ANY, fe=2) % pC8 (fe=2, ee=3, D384='C', D400='U') % FADD (rf=ANY, fe=4) % pC8 (fe=4, ee=3, D384='C', D400='U') >>
     pC8 (fe=ANY, ee=1, D384='C', D400='U') % flipL (fe=ANY, ee=1, D384='C') +
     FADD (rf=ANY, fe=None) + FADD (rf=ANY, fe=None) + pC8 (fe=None, ee=1, D384='C',D400='C') % pC8 (fe=None, ee=1, D384='C',D400='C'), 
     kc41)
 
#Cleaved HomoD cleaves Bid ?????
Parameter('kc42', 0.0697394e-3)
Rule('Cl_Homo_cat_Bid', pC8 (fe=ANY, ee=1, D384='C', D400='U') % pC8 (fe=ANY, ee=1, D384='C', D400='U') + Bid () >>
     pC8 (fe=ANY, ee=1, D384='C', D400='U') % pC8 (fe=ANY, ee=1, D384='C', D400='U') + tBid (), kc42)

#Cleaved HeteroD cleaves Bid ?????
Parameter('kc43', 0.0166747e-3)
Rule('Cl_Hetero_cat_Bid', pC8 (fe=ANY, ee=1, D384='C', D400='U') % flipL (fe=ANY, ee=1, D384='C') + Bid () >>
     pC8 (fe=ANY, ee=1, D384='C', D400='U') % flipL (fe=ANY, ee=1, D384='C') + tBid (), kc43)

#p18 cleaves Bid ?????
Parameter('kc44', 0.0000479214e-3)
Rule('p18_Bid_cat', pC8 (fe=None, ee=1, D384='C',D400='C') % pC8 (fe=None, ee=1, D384='C',D400='C') + Bid () >> 
	pC8 (fe=None, ee=1, D384='C',D400='C') % pC8 (fe=None, ee=1, D384='C',D400='C') + tBid (), kc44) 


# Fig 4B

Observe('p18', pC8(fe=None, ee=1, D384='C',D400='C') % pC8(fe=None, ee=1, D384='C',D400='C'))
Observe('tBid', tBid() )




# generate initial conditions from _0 parameter naming convention
for m in model.monomers:
    ic_param = model.parameters.get('%s_0' % m.name, None)
    if ic_param is not None:
        sites = {}
        for s in m.sites:
            if s in m.site_states:
                sites[s] = m.site_states[s][0]
            else:
                sites[s] = None
        Initial(m(sites), ic_param)


####



if __name__ == '__main__':
    from pysb.tools.export_bng_net import run as run_export_net
    print run_export_net(model)


