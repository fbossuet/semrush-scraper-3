DOCU, il estime si c'est une évolution ou un fix ensuite il regarde la documentation, fais une analyse de comment tout ca doit s'intégrer à la documentation (niveau de précision de l'info, contradictions possibles, etc.), il fait la modif de doc + il ajoute un résumé de tout le chat et de ce qu'il a touché au code dans un dossier historique ou il nomme le .md pareil que le commit avec le mot FIX ou EVOL au début et la date. Ensuite il commit.
Et je fais un chat par sujet, évol ou fix et à la fin de chaque chat quand je suis satisfait j'écris DOCU.

1. le code développé est il un fix ou une évolution ?
2. de nouveaux éléments ont ils été ajoutés par rapport à la doc ? 
    2.1. si non vérifier la conformité avec la doc
    2.2. si oui analyser comment intégrer les nouveautés à la doc : niveau de précision de l'information, contradictions possibles, etc.)
        2.2.1. y a t'il des questions à poser ? si oui les poser si non mettre à jour le doc
        2.2.2. mettre à jour la doc et créer un fichier .md avec un résumé de tout le chat, de tous les fichiers édités, et des modifications apportés dans un répertoire /historique à la racine du repertoire principal. 
        Le fichier doit être prévixé par FIX s'il s'agit d'une corection ou EVOL s'il s'agit d'une évolution suivi de la date du jour, suivi du titre du commit. Par exemple FIX-20250925-CONNEXON BDD.md
        Puis faire un commit avec exactement le même nom, et une description concis
