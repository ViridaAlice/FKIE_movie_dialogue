Dataset Explaination: 
-> /movies : contains folders of movie-names (spaces turned to -) which contain:
            movies released between 1.1.24 and 1.3.25, official scripts (nominated/handed in for script writing awards), none based on real people / biographies:
Movies contained within the corpus: A Different Man, All We Imagine as Light, Anora, A Real Pain, Babygirl, Blink Twice, Brutalist, Conclave, Daddio, Didi, Heretic, His Three Daughters, Hitman, I'm still here, I Saw the TV Glow, Juror 2, Memoir of a Snail, Nickel Boys, Nightbitch, Queer, The Last Showgirl, Thelma, The Piano Lesson, The Room Next Door, The Seed of the Sacred Fig, The Substance, The Wild Robot, Wicked 
            -> chars: all characters of the script in lowercase, separated by \n
            -> chars_dict: all characters and how often they appear in the script
            -> script: full script of the movie
-> dialogue_interactions: folders of movie-names containing text files of all character pairs that interact more than 10 times
    -> naming convention: "movie-name"+"_"+charactername1+"_"+charactername2+".json":
        contain List of all Interactions between the two characters, separated as List of all uttered words per Interaction. Every item within Interaction contains .json Object with "Character": character name, "dialogue": dialogue string, "movie": movie-name
    -> folder within the movie-name "relationships":
        contains a "_relationships" suffix json file for each character pair in the upper folder. 
        each file contains list of .json objects of the structure:
    [interaction-ID within pair] : {
        "relationship": [Platonic/Romantic/Antagonistic/Professional/Familial],
        "evidence" : [
                       { "line_indices" : [nr of lines by ID within conversation that prove the listed relationship],
                         "text" : [copied text of interaction evidence],
                         "type" : [Implied/Definitive]
                        }]} ...

