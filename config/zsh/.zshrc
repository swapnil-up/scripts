# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH

# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time Oh My Zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="robbyrussell"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
# zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"
# --- History Settings ---
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000

# Zsh equivalents to your bash history options
setopt EXTENDED_HISTORY          # Write the history file in the ":start:elapsed;command" format.
setopt SHARE_HISTORY             # Share history between all sessions.
setopt HIST_EXPIRE_DUPS_FIRST    # Expire duplicate entries first when trimming history.
setopt HIST_IGNORE_ALL_DUPS          # Don't record an entry that was just recorded to history.
setopt HIST_IGNORE_SPACE         # Don't record an entry starting with a space.
setopt HIST_VERIFY               # Don't execute immediately upon history expansion.

setopt HIST_IGNORE_ALL_DUPS  # Keep history cleanh

[ -f /usr/share/doc/fzf/examples/key-bindings.zsh ] && source /usr/share/doc/fzf/examples/key-bindings.zsh
[ -f /usr/share/doc/fzf/examples/completion.zsh ] && source /usr/share/doc/fzf/examples/completion.zsh

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)

source $ZSH/oh-my-zsh.sh

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
if [[ -n $SSH_CONNECTION ]]; then
  export EDITOR='vim'
else
  export EDITOR='nvim'
fi

# Compilation flags
# export ARCHFLAGS="-arch $(uname -m)"

# Set personal aliases, overriding those provided by Oh My Zsh libs,
# plugins, and themes. Aliases can be placed here, though Oh My Zsh
# users are encouraged to define aliases within a top-level file in
# the $ZSH_CUSTOM folder, with .zsh extension. Examples:
# - $ZSH_CUSTOM/aliases.zsh
# - $ZSH_CUSTOM/macos.zsh
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

typeset -U path # Keep path unique (no duplicates)

# --- Path & Environment ---
# Add all your custom paths here
path=(
    "$HOME/.local/bin"
    "$HOME/.cargo/bin"
    "/var/lib/flatpak/exports/bin"
    "/.local/share/flatpak/exports/bin"
    "/usr/bin/flutter/bin"
    "$HOME/.pub-cache/bin"
    "/home/swap/.config/herd-lite/bin"
    "/opt/nvim/"
    "/usr/local/go/bin"
    "$HOME/.config/composer/vendor/bin"
    "$path[@]" 
)
export PATH

# Node and PHP specific
export NODE_PATH=$NODE_PATH:$(npm root -g)
export PHP_INI_SCAN_DIR="/home/swap/.config/herd-lite/bin:$PHP_INI_SCAN_DIR"

# Editor
export EDITOR="nvim"
export VISUAL="nvim"

# --- Tool Init ---
eval "$(starship init zsh)"
eval "$(zoxide init zsh)"

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && path=("$PYENV_ROOT/bin" $path)
eval "$(pyenv init - zsh)"

# NVM (Node Version Manager)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Function to list files after every cd
chpwd() {
    ls -F --color=auto
}

# Dark mode, may not work on all apps and cause UI glitches
# export GTK_THEME=Adwaita-dark

# Clear screen on empty Enter
clear-empty-enter() {
    if [[ -z $BUFFER ]]; then
        # If the line is empty, clear the screen and accept the empty line
        clear
        zle accept-line
    else
        # If there is text, behave like a normal Enter key
        zle accept-line
    fi
}

# Register the function as a Zsh Line Editor (ZLE) widget
zle -N clear-empty-enter

# Bind the Enter key (standardly '^M') to our new widget
bindkey '^M' clear-empty-enter

# opencode
export PATH=/home/swap/.opencode/bin:$PATH
# lean 
export PATH=$HOME/.elan/bin:$PATH

# Source secrets
if [ -f ~/.env.secret ]; then
    source ~/.env.secret
fi

# whisper alias
alias whisper="~/github/scripts/scripts/utils/whisper.sh"
alias piper="~/github/scripts/scripts/utils/piper.sh"
