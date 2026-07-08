# PawPal+ Project Reflection

## 1. System Design
** Core user action

1. ADD a pet - enter the pet's name and type.
2. ADD a task - add a care task like a walk or feeding, with how long it takes and how important it is.
3. SEE today's plan - press a button to get a daily schedule of task in order.

**a. Initial design**

- Briefly describe your initial UML design.
My first UML design had four classes:
PET - holds the pet's name and type.
TASK - holds one care task: its title, how long it takes, and its priority.
Owner - holds the owner's name and how much time they have that day.
Scheduler - takes the tasks and the owner's time and builds the daily plan.

- What classes did you include, and what responsibilities did you assign to each?

I made Pet, Task, and Owner simple classes that just hold info, and let the Scheduler do the actual work of picking and ordering tasks into a plan.

**b. Design changes**

- Did your design change during implementation?

Yes, my design changed. At first my four classes didn't connect to each other, so I fixed three things:

- If yes, describe at least one change and why you made it.

1. I gave Owner lists of its pets and tasks, so the owner actually holds them.
2. I made Scheduler take the Owner instead of a separate time number, so the time is only stored in one place.
3. I added a Plan class to hold the finished schedule — which tasks got a time and which got skipped.

I did this because the original classes couldn't talk to each other, so there was no way to build a real plan.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

My scheduler warns about any two tasks that overlap in time, even if they belong
to different pets. I did this because one person can't really walk the dog and
feed the cat at the same minute. The downside is it sometimes warns when it
doesn't need to, like a nap that I don't have to sit there for. I figured it's
better to get an extra warning than to miss a real clash and forget to feed a pet.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
