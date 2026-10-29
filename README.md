In the landscape of “software tooling for Latin pedagogy”, William Whittaker’s Words, or
Whittaker’s Words, is the dominant player. Whittaker’s Words provides a comprehensive Latin
dictionary that allows users to look up any form of a Latin word and returns a candidate list of
possible definitions, along with the relevant grammatical information (such as case, for nouns,
or tense and mood, for verbs) of the particular form that was searched. 

The implementation ofsuch an engine is straightforward; given a sufficiently complete dictionary 
where all forms areannotated, determining the grammatical information associated with a word reduces to a
database lookup. This simple backend powers a tool that is near-universally utilized by Latin
students in the common challenge of identifying an unfamiliar Latin word or form. 

Another common challenge faced by Latin students, which as of yet does not have a large-scale
solution, is extracting metrical information from a line of Latin verse. In poetry, meter refers to 
the rhythmic structure of a verse. While English meter is based on stress, Latin meter is determined
by the ordering of long and short syllables, or the syllable weight. The meter that most Latin students
are initially exposed to, Dactylic hexameter, consists of six metrical “feet”, and each foot follows a 
limited set of allowable patterns. A foot can either be a dactyl (long short short), a spondee (long long). The final two feet usually follow the pattern
of a dactyl, followed by either a spondee or a trochee ( long short). The final syllable of the last
foot, because of its variance, is noted as an anceps. 

Although rare, there are examples of the fifth foot being a spondee rather than a dactyl. Aside from the last two feet, the first four feet can
be any combination of dactyl or spondee, usually reflecting the natural syllable weight of the
words therein. However, the presence of consonant clusters at inter-word boundaries, elisions,
or the simple decision of a poet to override these rules under poetic license can all influence the
ultimate sequence of feet in each line. The practice of identifying this sequence is referred to as
scansion.

There is no existing reference platform for the task of Latin scansion in the same vein as
Whittaker’s Words. Creating such a tool would be valuable both for students learning to read
Latin poetry and for researchers interested in computational approaches to understanding
classical texts. Because the space of possible lines of Latin verse is much larger than that of
Latin words themselves, the backend of such a tool would have to perform some kind of
operation akin to the human task of scanning, rather than searching through a database. Thus,
my goal for this project is to design and implement an engine that can, given some Latin verse
in Dactylic hexameter, apply the rules discussed above to accurately scan each line.
