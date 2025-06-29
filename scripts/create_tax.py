import sys, os
import gzip
import pandas as pd
import lzma

def create_tax_ref(nodes, names):
    name_dict = {}
    with open(names) as f:
        for line in f:
            node, p1, name, p2, other, p3, name_type = line.split("\t")[:7]
            if name_type == "scientific name":
                name_dict[node] = name
    graph = {}
    prefix_dict = {}
    with open(nodes) as f:
        for line in f:
            node, p1, parent, p2, level = line.split("\t")[:5]
            if node != parent:
                graph[node] = parent
            if level == "superkingdom":
                prefix_dict[node] = "d__"
            elif level == "species" or level == "strain":
                if level == "species":
                    prefix_dict[node] = "s__"
            elif level in  ["kingdom", "phylum", "class", "order", "family", "genus"]:
                prefix_dict[node] = level[0] + "__"
    return graph, name_dict, prefix_dict


def get_phylo_name(node):
    alist = [node]
    current = node
    while current in graph:
        current = graph[current]
        alist.append(current)
        if current in prefix_dict and prefix_dict[current] == "d__":
            break
    alist.reverse()
    taxstring = ""
    for i in alist:
        if i in prefix_dict:
            taxstring += ';' + prefix_dict[i] + name_dict[i]
    if taxstring == "":
        taxstring = "missing"
    return(taxstring[1:])


def process_virus(viral_fasta, viral_faa, virus_taxids, virus_prot_taxids, fasta_outdir, taxfile):
    try:
        os.makedirs(fasta_outdir)
    except FileExistsError:
        pass
    fasta_dict = {}
    tax_id_dict = {}
    with gzip.open(viral_fasta, 'rt') as f, open(virus_taxids, 'r') as taxids:
        virus_taxids_df = pd.read_csv(taxids, sep="\t", header=None, names=["accession", "tax_id"])
        for line in f:
            if line.startswith(">"):
                name = line.strip().lstrip('>')
                accession = name.split('|')[2]
                if accession in fasta_dict:
                    fasta_dict[accession][name] = ""
                else:
                    fasta_dict[accession] = {name:""}
                    normalised_accession = accession.split(".")[0]
                    if normalised_accession in virus_taxids_df['accession'].values:
                        taxid = str(virus_taxids_df.loc[virus_taxids_df['accession'] == normalised_accession, 'tax_id'].values[0])
                    else:
                        taxid = "missing"
                    tax_id_dict[accession] = taxid
            elif line.startswith('--'):
                pass
            else:
                fasta_dict[accession][name] += line.rstrip()
    with open(taxfile, 'w') as taxout:
        for i in fasta_dict:
            with open(os.path.join(fasta_outdir, i + ".fna"), 'w') as o:
                for j in fasta_dict[i]:
                    o.write(">{}\n{}\n".format(j, fasta_dict[i][j]))
            taxname = get_phylo_name(tax_id_dict[i])
            if taxname == "missing":
                taxname = "d__Viruses;missing"
            taxout.write("{}\t{}\t{}\n".format(i, os.path.join(fasta_outdir, i + ".fna"), taxname))
    with lzma.open(viral_faa, 'rt') as f, open(virus_prot_taxids, 'r') as taxids:
        virus_taxids_df = pd.read_csv(taxids, sep="\t", header=None, names=["accession", "tax_id"])
        for line in f:
            if line.startswith(">"):
                name = line.strip().lstrip('>')
                accession = name.split('|')[2]
                if accession in fasta_dict:
                    fasta_dict[accession][name] = ""
                else:
                    fasta_dict[accession] = {name:""}
                    normalised_accession = accession.split(".")[0]
                    if normalised_accession in virus_taxids_df['accession'].values:
                        taxid = str(virus_taxids_df.loc[virus_taxids_df['accession'] == normalised_accession, 'tax_id'].values[0])
                    else:
                        taxid = "missing"
                    tax_id_dict[accession] = taxid
            elif line.startswith('--'):
                pass
            else:
                fasta_dict[accession][name] += line.rstrip()
    with open(taxfile, 'r') as taxout:
        for i in fasta_dict:
            with open(os.path.join(fasta_outdir, i + ".faa"), 'w') as o:
                for j in fasta_dict[i]:
                    o.write(">{}\n{}\n".format(j, fasta_dict[i][j]))
            taxname = get_phylo_name(tax_id_dict[i])
            if taxname == "missing":
                taxname = "d__Viruses;missing"
            taxout.write("{}\t{}\t{}\n".format(i, os.path.join(fasta_outdir, i + ".faa"), taxname))

def process_euk(infile, outfile):
    with open(infile) as f, open(outfile, 'w') as o:
        for line in f:
            accession, taxid, fasta, gff = line.rstrip().split("\t")
            phylo_name = get_phylo_name(taxid)
            if phylo_name == "missing":
                phylo_name = "d__Eukaryota;missing"
            o.write("{}\t{}\n".format(accession, phylo_name))


graph, name_dict, prefix_dict = create_tax_ref(snakemake.input.nodes, snakemake.input.names)

if snakemake.params.dataset == "virus":
    process_virus(snakemake.input.rvdb_fasta, snakemake.input.rvdb_faa, snakemake.input.virus_taxids, snakemake.input.virus_prot_taxids, snakemake.params.virus_dir, snakemake.output.virus_tax)
elif snakemake.params.dataset == "euk":
    process_euk(snakemake.input.euk_list, snakemake.output.euk_tax)