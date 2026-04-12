# Midterm Deliverables – Additional Notes

## Context
This README documents additional analysis performed after the initial midterm deliverables were generated.

Due to Google’s March 2025 policy update, Gemini API (Google AI Studio) no longer applies Free Trial credits. Following TA guidance, we switched all subsequent LLM usage to **Vertex AI**.

---

## sympy__sympy-16792 (Vertex AI Analysis)

- **Status:** Exceeded limits (by design)
- **Analysis Tool:** Vertex AI (Gemini 3.1 Flash Lite)
- **Related Files:** `sympy__sympy-16792.traj.json`

### Summary of Failure
The failure occurs in SymPy’s `autowrap` module when generating Cython wrappers for functions that expect raw C pointer arguments (`double *`).

The generated wrapper attempts to expose a Python-facing function with a `double *` argument:

```cython
def autofunc_c(double * x):
    return autofunc(x)