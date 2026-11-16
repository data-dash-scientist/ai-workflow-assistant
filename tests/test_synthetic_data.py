from src.synthetic_data import CATEGORIES, generate_tickets


def test_generate_tickets_count():
    tickets = generate_tickets(n=30, seed=1)
    assert len(tickets) == 30


def test_generate_tickets_reproducible():
    a = generate_tickets(n=20, seed=7)
    b = generate_tickets(n=20, seed=7)
    assert [t.text for t in a] == [t.text for t in b]
    assert [t.ticket_id for t in a] == [t.ticket_id for t in b]


def test_generate_tickets_categories_valid():
    tickets = generate_tickets(n=25, seed=3)
    for t in tickets:
        assert t.true_category in CATEGORIES


def test_generate_tickets_distribution_balanced():
    tickets = generate_tickets(n=50, seed=42)
    counts = {c: 0 for c in CATEGORIES}
    for t in tickets:
        counts[t.true_category] += 1
    # 50 tickets / 5 catégories = 10 par catégorie (répartition stricte)
    for c in CATEGORIES:
        assert counts[c] == 10
