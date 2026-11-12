# Shell profile for the isolated lab terminal (mirrors the CKA exam setup).
[[ -f /usr/share/bash-completion/bash_completion ]] && source /usr/share/bash-completion/bash_completion
source <(kubectl completion bash)
alias k=kubectl
complete -o default -F __start_kubectl k
export EDITOR=vim KUBE_EDITOR=vim
export do='--dry-run=client -o yaml'
PS1='\[\e[36m\]cka:d${CKA_DAY:-??}\[\e[0m\] \[\e[2m\]${CKA_NS}\[\e[0m\] \w \$ '
cd /workspace
cat <<MSG
Isolated lab shell — namespace ${CKA_NS} is the default. Your files: /workspace/answers
Shortcuts: k=kubectl, \$do='--dry-run=client -o yaml', tab completion enabled.
MSG
