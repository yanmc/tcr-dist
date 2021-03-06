from basic import *
import cdr3s_human
from scipy.cluster import hierarchy
from scipy.spatial import distance
import os
import html_colors
import parse_tsv

verbose = __name__ == '__main__'

def get_rep( gene, organism ):
    assert gene.startswith('TR')
    vj = gene[3]
    if vj == 'V':
        rep = cdr3s_human.all_loopseq_representative[ organism ][ gene ]
    else:
        rep = cdr3s_human.all_jseq_representative[ organism ][ gene ]
    return rep


def get_mm1_rep( gene, organism ):
    assert gene.startswith('TR')
    vj = gene[3]
    if vj == 'V':
        rep = cdr3s_human.all_loopseq_representative_mm1[ organism ][ gene ]
    else:
        rep = cdr3s_human.all_jseq_representative[ organism ][ gene ]
    return rep


def get_rep_ignoring_allele( gene, organism ):
    rep = get_rep( gene, organism )
    rep = rep[:rep.index('*')]
    return rep



def tree_sort( old_l, distances, return_leaves=True ): ## average linkage
    assert len(distances) == len(old_l)

    if len(old_l)==1:
        leaves = [0]
    else:
        y = distance.squareform( distances, checks=True )
        Z = hierarchy.average( y )
        #c,coph_dists = hierarchy.cophenet(Z,y)
        leaves = hierarchy.leaves_list( Z )

    new_l = [ old_l[x] for x in leaves ]

    if not return_leaves:
        return new_l
    else:
        return new_l, leaves

def get_top_genes( blast_hits_string ):
    hits = dict( [ ( x.split(':')[0], int( x.split(':')[1] ) ) for x in blast_hits_string.split(';') ] )
    top_score = max( hits.values() )
    return set( [ x for x,y in hits.iteritems() if y >= top_score ] )

def get_top_reps( blast_hits_string, organism ):
    hits = dict( [ ( x.split(':')[0], int( x.split(':')[1] ) ) for x in blast_hits_string.split(';') ] )
    top_score = max( hits.values() )
    vj = hits.keys()[0][3]
    if vj == 'V':
        rep_map = cdr3s_human.all_loopseq_representative[ organism ]
    else:
        assert vj == 'J'
        rep_map = cdr3s_human.all_jseq_representative[ organism ]
    return set( [ rep_map[x] for x,y in hits.iteritems() if y >= top_score ] )


def reps_from_genes( genes, organism, mm1=False, trim_allele=False ):
    ## if genes is a set we can't index into it
    vj = [ x[3] for x in genes ][0]

    if vj == 'V':
        if mm1:
            rep_map = cdr3s_human.all_loopseq_representative_mm1[ organism ]
        else:
            rep_map = cdr3s_human.all_loopseq_representative[ organism ]
    else:
        assert vj == 'J'
        rep_map = cdr3s_human.all_jseq_representative[ organism ]

    reps = set( [ rep_map[x] for x in genes ] )
    if trim_allele:
        reps = set( ( x[:x.index('*')] for x in reps ) )
    return reps

def readme( pngfile, text ):
    """Generate some readme text associated to an image file, that will be incorporated into the
    big html results file by run_basic_analysis.py"""

    out = open(pngfile+'.readme','w')
    cmd = ' '.join(argv)
    out.write("""
<u>Command</u>:
{}
<br><br>
<u>Filename</u>:
{}
<br><br>
<u>Readme</u>:
{}
<br><br>
""".format(cmd, pngfile, text))
    out.close()


## setup a mapping that we can use for counting when allowing mm1s and also ignoring alleles

allele2mm1_rep_gene_for_counting = {}
def get_mm1_rep_ignoring_allele( gene, organism ): # helper fxn
    rep = get_mm1_rep( gene, organism )
    rep = rep[:rep.index('*')]
    return rep

for organism in ['human','mouse']:
    allele2mm1_rep_gene_for_counting[ organism ] = {}

    for chain in 'AB':

        ## look at gene/allele maps
        ## V
        vj_alleles = { 'V': [ x for x in cdr3s_human.all_loopseq_representative[ organism ].keys() if x[2] == chain ],
                       'J': [ x for x in cdr3s_human.all_jseq_representative[ organism ].keys() if x[2] == chain ] }

        for vj, alleles in vj_alleles.iteritems():
            gene2rep = {}
            gene2alleles = {}
            rep_gene2alleles = {}

            for allele in alleles:
                assert allele[2] == chain
                gene = allele[:allele.index('*')]
                rep_gene = get_mm1_rep_ignoring_allele( allele, organism )
                if rep_gene not in rep_gene2alleles:
                    rep_gene2alleles[ rep_gene ] = []
                rep_gene2alleles[ rep_gene ].append( allele )

                if gene not in gene2rep:
                    gene2rep[gene] = set()
                    gene2alleles[gene] = []
                gene2rep[ gene ].add( rep_gene )
                gene2alleles[gene].append( allele )

            merge_rep_genes = {}
            for gene,reps in gene2rep.iteritems():
                if len(reps)>1:
                    assert vj=='V'
                    if verbose:
                        print 'multireps:',organism, gene, reps
                        for allele in gene2alleles[gene]:
                            print cdr3s_human.all_merged_loopseqs[organism][allele], allele, \
                                get_rep(allele,organism), get_mm1_rep(allele,organism)

                    ## we are going to merge these reps
                    ## which one should we choose?
                    l = [ (len(rep_gene2alleles[rep]), rep ) for rep in reps ]
                    l.sort()
                    l.reverse()
                    assert l[0][0] > l[1][0]
                    toprep = l[0][1]
                    for (count,rep) in l:
                        if rep in merge_rep_genes:
                            assert rep == toprep and merge_rep_genes[rep] == rep
                        merge_rep_genes[ rep ] = toprep


            for allele in alleles:
                count_rep = get_mm1_rep_ignoring_allele( allele, organism )
                if count_rep in merge_rep_genes:
                    count_rep = merge_rep_genes[ count_rep ]
                allele2mm1_rep_gene_for_counting[ organism ][ allele] = count_rep
                if verbose:
                    print 'allele2mm1_rep_gene_for_counting:',organism, allele, count_rep

def get_mm1_rep_gene_for_counting( allele, organism ):
    global allele2mm1_rep_gene_for_counting
    return allele2mm1_rep_gene_for_counting[ organism ][ allele ]


def countreps_from_genes( genes, organism ):
    global allele2mm1_rep_gene_for_counting
    reps = set( ( allele2mm1_rep_gene_for_counting[ organism ][ x ] for x in genes ) )
    return reps


def assign_label_reps_and_colors_based_on_most_common_genes_in_repertoire( tcr_infos, organism ):
    ## assumes that each element of tcr_infos is a dictionary with fields that would have come from parse_tsv_line
    ## uses the *_countreps info that was filled in by read_pair_seqs.py
    ## the _label_rep* fields get over-written if they were present
    for segtype in segtypes_lowercase:
        countreps_tag = segtype+'_countreps'
        rep_tag       = segtype+'_label_rep'
        color_tag     = segtype+'_label_rep_color' ## where we will store the rep info

        counts = {}
        for tcr_info in tcr_infos:
            reps = tcr_info[countreps_tag].split(';')
            for rep in reps:
                counts[rep] = counts.get(rep,0)+1

        newcounts = {}
        for tcr_info in tcr_infos:
            reps = tcr_info[countreps_tag].split(';')
            toprep = max( [ ( counts[x],x) for x in reps ] )[1]
            tcr_info[rep_tag] = toprep ## doesnt have allele info anymore
            newcounts[toprep] = newcounts.get(toprep,0)+1

        l = [(y,x) for x,y in newcounts.iteritems()]
        l.sort()
        l.reverse()
        rep_colors = dict( zip( [x[1] for x in l], html_colors.get_rank_colors_no_lights(len(l)) ) )
        for tcr_info in tcr_infos:
            tcr_info[ color_tag ] = rep_colors[ tcr_info[ rep_tag ] ]

    return ## we modified the elements of the tcr_infos list in place


## this is not exactly perfect, but probably OK to start with...
##
def detect_fake_chains( clones_file, Achain='A', Bchain='B' ):
    tcrs = parse_tsv.parse_tsv_file( clones_file, key_fields = [], store_fields = ['va_gene','cdr3a','vb_gene','cdr3b'] )
    fake_chains = []
    if len( set( [ (x[0],x[1]) for x in tcrs ] ) )==1:
        fake_chains.append( Achain )
    if len( set( [ (x[2],x[3]) for x in tcrs ] ) )==1:
        fake_chains.append( Bchain )
    if fake_chains:
        print 'Fake sequence data detected for chains: {}'.format( ' '.join( fake_chains ) )
    return fake_chains


# if __name__ == '__main__':
#     for organism in allele2mm1_rep_gene_for_counting:
#         for allele in allele2mm1_rep_gene_for_counting[ organism ]:
#             print 'get_mm1_rep_gene_for_counting
