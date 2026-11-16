from src.classifier import RuleBasedClassifier


def test_classify_devis():
    clf = RuleBasedClassifier()
    result = clf.classify("Quel est le prix d'un devis pour une table ?", "Awa")
    assert result.category == "devis"
    assert 0 <= result.confidence <= 1


def test_classify_reclamation():
    clf = RuleBasedClassifier()
    result = clf.classify("La finition présente une rayure, je ne suis pas satisfait", "Moussa")
    assert result.category == "reclamation"


def test_classify_spam():
    clf = RuleBasedClassifier()
    result = clf.classify("Vous avez gagné un bon d'achat, cliquez ici", "Inconnu")
    assert result.category == "spam"


def test_classify_response_contains_sender_name():
    clf = RuleBasedClassifier()
    result = clf.classify("Pouvez-vous me donner un devis pour ce meuble ?", "Khady")
    assert "Khady" in result.suggested_response
