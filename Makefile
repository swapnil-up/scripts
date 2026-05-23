.PHONY: format lint

SHELL_FILES := $(shell find scripts setup config -name '*.sh' 2>/dev/null) \
              config/bash/.bashrc config/zsh/.zshrc config/bash/.profile
PYTHON_FILES := $(shell find scripts -name '*.py' 2>/dev/null)

format:
	shfmt -w -s $(SHELL_FILES)
	black $(PYTHON_FILES)

lint:
	bash -n $(SHELL_FILES)
	python3 -m py_compile $(PYTHON_FILES) 2>/dev/null; true
