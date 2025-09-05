---
name: "Agent Episodic Memory"
description: "System message for agent episodic memory and task completion patterns"
version: "1.0"
author: "Assistant"
tags: ["memory", "episodic", "task-patterns", "learning"]
required_variables: []
optional_variables: {}
template_engine: "jinja2"
cache: true
---

## system

After finishing the task, summarize the successful steps to finish the task to `memory-<summarized topic less than 10 words>.md` (DO NOT treat this as URL) file as memory for future reference. 

### Memory Instructions
* Based on the successful steps to finish target task, summarize the fastest way to finish the task.
* Make the memory as a general method wiout specific task info, such as Amazon stock in this case.
* If there is a method that is not stable to finish the task, you can use other methods to finish the task. But keep them both in the memory.
* The successful way takes higher priority than the other methods in the memory.

### Memory Format
* Each task-finishing memory is a markdown file with the following format:
    * Section **Task Aim**: The aim of the task.
    * Section **Steps**: The steps to finish the task.
    * Section **Alternatives**: The alternatives to finish the task.
    * Section **Notes**: Notes about the task.