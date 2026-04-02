from matplotlib import pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(11, 4.8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 5)
ax.axis('off')

boxes = [
    (0.4, 2.9, 2.1, 1.1, "Flux d'annonces\nà surveiller"),
    (2.9, 2.9, 2.2, 1.1, "Trois indicateurs\nprix, similarité, profil"),
    (5.5, 2.9, 2.1, 1.1, "Indice de risque\net seuils"),
    (8.0, 3.25, 3.1, 0.75, "Risque acceptable :\nveille, journalisation, suivi"),
    (8.0, 2.15, 3.1, 0.75, "Risque défavorable :\nrevue humaine, préservation, alerte"),
    (2.9, 0.8, 2.8, 1.0, "Journal d'audit\n+ retour d'expérience"),
    (6.2, 0.8, 3.5, 1.0, "Ajustement des seuils\net enrichissement du modèle"),
]

for x,y,w,h,label in boxes:
    rect = patches.FancyBboxPatch((x,y), w,h, boxstyle="round,pad=0.02,rounding_size=0.04", linewidth=1.2, edgecolor="#30465a", facecolor="#eaf1f7")
    ax.add_patch(rect)
    ax.text(x+w/2, y+h/2, label, ha='center', va='center', fontsize=10)

arrows = [
    ((2.5,3.45),(2.9,3.45)),
    ((5.1,3.45),(5.5,3.45)),
    ((7.6,3.45),(8.0,3.62)),
    ((7.6,3.45),(8.0,2.52)),
    ((5.5,2.9),(4.5,1.8)),
    ((5.7,1.3),(6.2,1.3)),
    ((7.3,1.8),(7.3,2.9)),
    ((8.9,2.15),(8.9,1.8)),
]
for (x1,y1),(x2,y2) in arrows:
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1), arrowprops=dict(arrowstyle='->', lw=1.4, color='#30465a'))

ax.text(0.4, 4.45, "Logique opérationnelle du modèle actionnable", fontsize=14, fontweight='bold')
ax.text(0.4, 4.1, "Le modèle sert au triage précoce et non à l'administration autonome d'une preuve judiciaire.", fontsize=9.5, color='#4A5560')
fig.tight_layout()
fig.savefig('figures/operational_workflow_fr.png', dpi=220, bbox_inches='tight')
