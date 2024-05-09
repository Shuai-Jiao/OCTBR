# Object-Centric Token-Based Replay
This repository provides a conformance checking method called object-centric token-based replay, which is an appropriate translation of the traditional token-based replay method to the object-centric level. This method considers the intricate interactions and interdependencies between different objects involved in events, which are neglected in traditional methods. The evaluation is based on token operations during the replay, where irregular token operations are considered as penalization to fitness measurement. This implementation contributes an option to perform conformance checking and outstands in significant scalability and efficiency.

## Installation
The application environment is documented in requirements.txt, so please set up the necessary packages by 'pip install -r requirements.txt' before the usage.

## Usage
Since the implementation of this method is based on OCPA, the input log or model should be in OCPA format. By recalling function token_based_replay(ocel,ocpn) imported from module object_centric_token_based_replay, the object-centric token-based replay method is carried out for evaluating the given object-centric event log and object-centric Petri net, where optional configurations are the approach of backward replay, resolution of token flooding, and the application of caching.

Then, a dictionary of evaluation results is returned, which contains the following information:
'fitness': the fitness value of the evaluation, reflecting how the input model could reflect the input log.
'p': the number of produced tokens during the replay.
'c': the number of consumed tokens during the replay.
'm': the number of missing tokens during the replay.
'r': the number of remaining tokens during the replay.
'f': the number of frozen tokens during the replay.
'is_equal': check whether the replay satisfies the flow conservation.
'explicit_missing_tokens': the explicit missing tokens during the replay.
'implicit_missing_tokens': the implicit missing tokens during the replay.
'remaining_tokens': the remaining missing tokens during the replay.
'frozen_tokens': the frozen tokens during the replay.
'unenabled_transitions': the transitions unenabled for the execution during the replay.
Further information such as the problematic places or problematic objects for certain behaviors during the replay could be extracted from the returned values above.

