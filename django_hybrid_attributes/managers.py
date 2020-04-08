from django.db import models

from .core import HybridExpressionResult


class HybridQuerySetMixin(object):

    def filter(self, *args, **kwargs):
        hybrid_expression_results = []
        common_filter_args = []

        for arg in args:
            if isinstance(arg, HybridExpressionResult):
                hybrid_expression_results.append(arg)
            else:
                common_filter_args.append(arg)

        self = super().filter(*common_filter_args, **kwargs)

        for hybrid_expression_result in hybrid_expression_results:
            self = hybrid_expression_result._apply_filter(queryset=self)

        return self


class HybridQuerySet(HybridQuerySetMixin, models.QuerySet):
    pass


class HybridManagerMixin(object):
    def get_queryset(self):
        return HybridQuerySet(self.model, using=self._db)

    def filter(self, *args, **kwargs):
        return self.get_queryset().filter(*args, **kwargs)


class HybridManager(HybridManagerMixin, models.Manager):
    pass
