import json

with open("results/o3_relevance_reference.json", "r", encoding="utf-8") as f:
    reference = json.load(f)

with open("results/o3_improved_relevance.json", "r", encoding="utf-8") as f:
    improved = json.load(f)


def is_relevant(result, query):
    price = result.get("price")
    title = result.get("title", "").lower()

    if query == "laptop for students":
        return (
            "laptop" in title
            and "student" in title
            and price <= 70000
        )

    if query == "budget programming laptop":
        return (
            "programming laptop" in title
            and price <= 60000
        )

    if query == "gaming laptop":
        return "gaming laptop" in title

    if query == "wireless headphones":
        return "wireless headphones" in title

    if query == "mobile phone":
        return "mobile phone" in title

    return False


print("=" * 70)
print("CLOUD-30 O3 RELEVANCE COMPARISON")
print("=" * 70)

total_old = 0
total_new = 0
total_results = 0

for old, new in zip(
    reference["evaluation"],
    improved
):

    query = old["query"]

    new_results = new["results"]

    relevant_new = sum(
        is_relevant(result, query)
        for result in new_results
    )

    relevant_old = old["relevant"]
    count = len(new_results)

    old_p = relevant_old / count
    new_p = relevant_new / count

    total_old += relevant_old
    total_new += relevant_new
    total_results += count

    print(f"\nQuery: {query}")
    print(f"Baseline P@20 : {old_p * 100:.2f}%")
    print(f"Improved P@20 : {new_p * 100:.2f}%")
    print(
        f"Change        : "
        f"{(new_p - old_p) * 100:+.2f} percentage points"
    )

overall_old = total_old / total_results
overall_new = total_new / total_results

print("\n" + "=" * 70)
print("OVERALL RESULT")
print("=" * 70)

print(f"Baseline P@20 : {overall_old * 100:.2f}%")
print(f"Improved P@20 : {overall_new * 100:.2f}%")
print(
    f"Improvement   : "
    f"{(overall_new - overall_old) * 100:+.2f} percentage points"
)

result = {
    "baseline_p20": overall_old,
    "improved_p20": overall_new,
    "improvement_percentage_points":
        (overall_new - overall_old) * 100
}

with open(
    "results/o3_relevance_comparison.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(result, f, indent=2)

print("\nSaved:")
print("results/o3_relevance_comparison.json")