```
class coverage:
    MCP17:       1.0
    MCP112:      1.0
    MCP:         1.0
    Yarn17:      0.9722222222222222
    Yarn18:      0.9466230936819172
    Yarn:        0.985838779956427
    MCP+Yarn:    1.0
method coverage:
    MCP17:       0.3633416270828621
    MCP112:      0.22521299856744326
    MCP:         0.4041317952197844
    Yarn17:      0.3577621955816934
    Yarn18:      0.34878986654603034
    Yarn:        0.3761592399909523
    MCP+Yarn:    0.511724345924753
field coverage:
    MCP17:       0.6943478260869566
    MCP112:      0.5589855072463769
    MCP:         0.7846376811594203
    Yarn17:      0.7017391304347826
    Yarn18:      0.7163768115942029
    Yarn:        0.7644927536231884
    MCP+Yarn:    0.9034782608695652
parameter coverage:
    MCP17:       0.07404701534230092
    MCP112:      0.1374790493790021
    MCP:         0.18857707679745583
    Yarn17:      0.2630538484679187
    Yarn18:      0.17693068030426748
    Yarn:        0.276462245906571
    MCP+Yarn:    0.34522325841248014
total coverage:
    MCP17:       0.29091190244764514
    MCP112:      0.2624149509587346
    MCP:         0.37549703985155075
    Yarn17:      0.38643191658566756
    Yarn18:      0.3407263409030662
    Yarn:        0.4088318458955554
    MCP+Yarn:    0.505655208977644
```

## Legend
* **MCP17**: 1.7:notch -> 1.7:srg -> 1.7:mcp
* **MCP112**: 1.7:notch -> 1.7:srg -> 1.12:mcp
* **MCP**: MCP17 + MCP112
* **Yarn17**: 1.7:notch -> 1.7:intermediary -> 1.7:yarn
* **Yarn18**: 1.7:notch -> 1.7:srg -> 1.8:notch -> 1.8:intermediary -> 1.8:yarn
* **Yarn**: Yarn17 + Yarn18
* **MCP+Yarn**: MCP + Yarn

Coverage is calculated in the following way: we iterate over every "notch" name, and attempt to map them through one of the above chains. The coverage value is the amount of names that successfully completed the chain divided by the amount of total names.
