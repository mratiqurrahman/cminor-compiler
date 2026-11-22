PYTHON ?= python3
COMPILER = ./cminorcc

.PHONY: test check examples capabilities

test:
	$(PYTHON) -m unittest discover -s tests -v

check:
	$(COMPILER) --check examples/loop_call_trace.cm

examples:
	@for source in examples/*.cm; do $(COMPILER) --check "$$source" || exit $$?; done

capabilities:
	$(COMPILER) --capabilities
