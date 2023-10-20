init:
	sh scripts/pre_tf.sh $(env_name)

plan:
	sh scripts/plan_changes.sh $(env_name)

apply:
	sh scripts/apply_changes.sh $(env_name)

fmt:
	terraform fmt -recursive
