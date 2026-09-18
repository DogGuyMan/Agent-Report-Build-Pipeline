```
abstractstage 
    transition_bitflag -> int
    curtransition -> int
    perform()
    transition()

llmstage : abstractstage
    getabstract_llm_prompt() : virtual function -> string
    perform() : virtual function
        os.cli("claude << 'getabstract_llm_prompt'");

rulebasestage : abstractstage
    perform() : virtual function


prep : rulebasestage
warmup : rulebasestage
survey-plan : rulebasestage
warmup-save : rulebasestage
terms : rulebasestage
build : rulebasestage
check: rulebasestage
... 

lang-select  : llmstage
survey  : llmstage
wiki  : llmstage
...

```

```
pipeline
    StageDAGGraph abstractstage
    run : virtual function -> next_stage

run_mode1 : pipeline
    run : override -> next_stage
        stages.foreach.perform()
    

```