# Offline-MapMatching
A <a href="https://github.com/qgis/QGIS">QGIS</a>-plugin for matching a trajectory with a network using a Hidden Markov Model and Viterbi algorithm.

## Goal of the project
Matching a trajectory with a network, e.g. a road network, is a classical task in geoinformatics.
It can be differentiated into online, i.e. during the measurement of the trajectory like in car navigation,
and offline, i.e. after the measurement of the trajectory, map matching. This plugin addresses only the offline map mathing.
<br>
Because of inaccuracies of the GNSS signal and/or a low data quality of the network, the positions of the trajectory
and the network are differing. In many cases a simple snapping of the trajectory on the network will not work. Reasons for that
can be e.g. outliers in the trajectory or crossings of edges in the network.
<br>
This plugin provides a statistical approach to solve the problem of offline map matching using the principles of 
Hidden Markov Models (HMM) and the Viterbi algorithm.

## Change log
1.0.0 - first release

## Hints for developement
- the plugin was created using the QGIS-plugin "plugin builder"
- all additional python files were created in the
<a href="https://github.com/jagodki/Offline-MapMatching/tree/master/src/offlinemapmatching/mm">mm</a>-folder

## Hints for usage
- the progress of the computation will be displayed with a progressbar (starts from zero for every computation step)
and written to the QGIS-log
- it is recommended to set the meaximum search distance as low as possible, because this setting has a very huge influence on the computation time
- it is recommended to use a low segmented network layer, because candidate points will be searched for
every linestring, i.e. the more linestrings can be found in the maximum search distance, the more candidates will be found
and the more computation time is needed
- use a metric CRS, because distances will be calculated
- the quality of the trajectory is very important for a good result, i.e. big outliers should be removed before running the plugin
(the algorithm does not know, which observation is an outlier, and searches the most likely path for the whole trajectory)
- the distance between two observations of the trajectory should be 100m maximum, a low distance results in a better map matching
- if positions where measured time-controlled, standing times should be removed before running the plugin


## Description of the computation
First the plugin calculates possible candidate points for each observation point in the trajectory (Budig 2012: 10).
The candidates will be arranged in a candidate graph with n layers, n = count of observation points (Budig 2012: 13).
After calculating different posibilities, the path with the highest posibility will be found using the Viterbi algorithm.
Following the different parts of the computation in a nutshell, followed by explicit descriptions of each step:
- read the input layers
- calculate candidate points for each trajectory point using the maximum search distance and store them in a graph
- calculate the probability for each candidate point to be emitted by the correpsonding trajectory point
- calculate the similarity of the transitions compared to the trajectory points
- find the best candidates using Viterbi algorithm
- create a layer of linestrings using this candidates

### read the input layers
The network and the trajectory layers will be imported into the plugin and the internal structur of objects will be initialised.
The trajectory cannot be imported, if the layer has no attribute fields.
Each position of the trajectory is called observation and one part of the five tupel of a Hidden Markov Model (HMM).

### calculate candidate points/create candidate graph
A candidate point is a possible position of an observation on the network.
The plugin searches the nearest points on every linestring for each observation.
If the distance between a candidate and the correpsonding observation is less or equal the maximum search distance,
the candidate will be added to the candidate graph (Budig 2012: 14):
<img src="screenshots/candidates.png" />
<br>
"A candidate graph is a directed acyclic graph (DAG) which represents all paths that are
considered possible final matching results for the given GPS trajectory" (Budig 2012: 13). The graph will be used as a stochastic matrix
for the HMM. The graph has n layers with n as the count of observations.
Each layer contains all candidates of the same/corresponding observation (Budig 2012: 13):
<img src="screenshots/graph.png" />
<br>
The calculation of candidates has a huge impact of the computation time. A higher search distance can result in more candidates per
observation and more possible paths, which will be calculated in the next steps. Also a high segmentation of the network can cause
a lot of candidates per observation with the same problem for the computation time.

### calculate emission probabilities
A GNSS-measured position is not the real position because of the inaccuracy of the GNSS signal. Also the quality of the network geometry
can be very low. Therefore the candidates are more or less away from the observations.
To calculate the probability, that an observation was emitted by a candidate, a normal distribution is postulated, i.e.
the probability is pending on the distance between observation and candidate and will be calculated using the normal distribution (Budig 2012: 13). The emission probabilities for each candidate are one part of the five tupel of a Hidden Markov Model (Haenelt 2007: 4-5). The emission probabilities of the candidates of the first observation will be used as initial state
probabilities in the HMM and represent another part of the five tupel (Raymond et al. 2012: 2244).
The expected value and the standard deviation can be set by the user. The expected value represents the best possible or expected distance between
a candidate and an observer. In most cases, this should be a value of zero.
The standard deviation is more tricky. Remember, that 95.45% of all possible values (in this case the distances between candidates and an observer)
are within 2*sigma, 99.73% within 3*sigma. In my tests I got good results setting the standard deviation equals (expected value) / (n) with
n between 2 and 3. A too high or too low standard deviation can overemphasise or underemphasise the emission probability (compared to the transition
probability) and maybe results in an incorrect map matching.

### calculate transition probabilities/similarities
Another and the last tupel of the HMM are the transition probabilities whereat transitions are connections between two candidates in the graph,
i.e. the edges of the graph. The plugin does not really calculate a probability for each transiton, but more similarities.
The transition between two candidates will be compared by the transition between the two corresponding observations. Two characteristics
of the transitions will be compared:
1. the distances
2. the directions
<br>
The euklidean distance between the two observations will be put in relation to the distance on the network between the two candidates (Budig 2012: 12).
The distance on the network will be calculated using the analysis framework of QGIS and the Dijkstra algorithm with the distance between nodes as
edge weight.
To receive a value between 0 and 1 (to use the result like a probability), the lower distance of this two distances will be divided by the higher
one (Budig 2012: 16).
<br>
The directions will be calculated using the slope of the two lines through both candidates respectively the observations.
The angle is the arcustanges of the slope and will have a value between 0 and 180 (the python function atan is used and the
result will be summed up by 90 to receive positive values). The difference of this two angles will be normalised to receive
a value between 0 and 1 (Budig 2012: 17):
<img src="screenshots/direction.png" />

### Viterbi algorithm
Using the Viterbi algorithm all probabilities (initial, emission and transition) along each path will be multiplied in an efficient way.
The Viterbi algorithm uses results of former calculations again to avoid multiple calculations of same sequences.
Also just the highest probabilities to reach a candidate will be stored and reused (Haenelt 2007: 12).
The most likely path through the HMM, i.e. the path through the candidate graph with the highest probability, is the result of this algorithm.

### store the path in a new layer
The founded Viterbi path represents the vertices of the resulting line. A routing between following points of the Viterbi path
returns linestrings, which will be written to a new memory layer. The plugin provides a style file, so that the new layer will be displayed as a
red line.

## Attribute Table of the resulting layer
#### id
an integer value as counter of the linestrings

#### total_probability_start
the total probability of the start vertex of the current linestring, i.e. the product
of the emission and transition probability of the start vertex and the total probability of the parent vertex/candidate

#### total_probability_end
the total probability of the end vertex of the current linestring, i.e. the product of the emission
and transition probability of the end vertex and the total probability of the parent vertex/candidate
(should be the start vertex of the current linestring)

#### emission_probability_start
the emission probability of the start vertex

#### emission_probability_end
the emission probability of the end vertex

#### transition_probability_start
the transition probability to reach the start vertex

#### transition_probability_end
the transition probability to reach the end vertex

#### observation_id_start
the id of the trajectory feature, which corresponds to the start vertex

#### observation_id_end
the id of the trajectory feature, which corresponds to the end vertex

## Screenshots of matched and unmatched trajectories
<table style="width:100%">
    <tr>
        <th>not successful matched</th>
        <th>successful matched</th> 
        <th>successful matched</th>
        <th>legend</th>
    </tr>
    <tr>
        <td><img src="screenshots/not_correct.png" /></td>
        <td><img src="screenshots/correct.png" /></td>
        <td><img src="screenshots/correct_2.png" /></td>
        <td><img src="screenshots/legend.png" /></td>
    </tr>
    <tr>
        <td>st. deviation = 10, max. search dist. = 25</td>
        <td>st. deviation = 10, max. search dist. = 25</td>
        <td>st. deviation = 12, max. search dist. = 30</td>
        <td></td>
    </tr>
</table>

## Sources
Budig, B. (2012). <i>An algorithm for map matching on incomplete road databases</i>. 
Retrieved Jul 31, 2018 from 
<a href="http://www1.pub.informatik.uni-wuerzburg.de/pub/theses/2012-budig-bachelor.pdf">http://www1.pub.informatik.uni-wuerzburg.de/pub/theses/2012-budig-bachelor.pdf</a>
<br><br>
Raymond, R., Morimura, T., Osogami, T., Hirosue, N. (2012). <i>Map Matching with Hidden Markov Model on Sampled Road Network</i>. 
21st International Conference on Pattern Recognition (ICPR 2012). 
Retrieved Jul 31, 2018 from 
<a href="http://f4k.dieei.unict.it/proceedings/ICPR2012/media/files/2224.pdf">http://f4k.dieei.unict.it/proceedings/ICPR2012/media/files/2224.pdf</a>
<br><br>
Haenelt, K. (2007). <i>Der Viterbi-Algorithmus. Eine Erl\ufffduterung der formalen Spezifikation am Beispiel des Part-of-Speech Tagging</i>. 
Retrieved Jul 31, 2018 from 
<a href="http://kontext.fraunhofer.de/haenelt/kurs/folien/Haenelt_Viterbi-Tutor.pdf">http://kontext.fraunhofer.de/haenelt/kurs/folien/Haenelt_Viterbi-Tutor.pdf</a>
<br>
