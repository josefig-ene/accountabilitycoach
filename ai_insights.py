"""
AI-Powered Insights Module
Generates intelligent recommendations and analysis for CEO Dashboard
"""

import os
from typing import List, Dict, Any, Optional

# Check if OpenAI is available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIInsights:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.use_openai = OPENAI_AVAILABLE and self.openai_key is not None

        if self.use_openai:
            openai.api_key = self.openai_key

    def generate_portfolio_insights(self, ideas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights about the idea portfolio"""

        if not ideas:
            return {
                'summary': "No ideas in portfolio yet.",
                'recommendations': [],
                'risk_analysis': "Add some ideas to get started!"
            }

        # Calculate basic metrics
        total_ideas = len(ideas)
        avg_confidence = sum(i['confidence_score'] for i in ideas) / total_ideas
        at_risk = [i for i in ideas if i.get('risk_flags', '')]
        high_confidence = [i for i in ideas if i['confidence_score'] >= 70]
        low_confidence = [i for i in ideas if i['confidence_score'] < 40]

        # Stage distribution
        stage_dist = {}
        for idea in ideas:
            stage = idea['stage']
            stage_dist[stage] = stage_dist.get(stage, 0) + 1

        if self.use_openai:
            # Use OpenAI for advanced insights
            return self._generate_openai_insights(ideas, {
                'total': total_ideas,
                'avg_confidence': avg_confidence,
                'at_risk_count': len(at_risk),
                'high_confidence_count': len(high_confidence),
                'low_confidence_count': len(low_confidence),
                'stage_distribution': stage_dist
            })
        else:
            # Fallback to rule-based insights
            return self._generate_rule_based_insights(ideas, at_risk, high_confidence, low_confidence, stage_dist)

    def _generate_rule_based_insights(self, ideas, at_risk, high_confidence, low_confidence, stage_dist):
        """Generate insights using predefined rules"""

        recommendations = []

        # Portfolio balance recommendations
        if stage_dist.get('seed', 0) > len(ideas) * 0.5:
            recommendations.append("🌱 Heavy on seed stage: Consider advancing some ideas to validation")

        if stage_dist.get('scale', 0) + stage_dist.get('exit', 0) == 0:
            recommendations.append("📈 No scaling ideas: Focus on moving pilot-stage ideas forward")

        # Risk recommendations
        if len(at_risk) > len(ideas) * 0.3:
            recommendations.append(f"⚠️ High risk concentration: {len(at_risk)} ideas flagged - prioritize risk mitigation")

        # Confidence recommendations
        if len(low_confidence) > 0:
            recommendations.append(f"🎯 {len(low_confidence)} ideas need milestone completion to boost confidence")

        if len(high_confidence) > 0:
            recommendations.append(f"✨ {len(high_confidence)} ideas are ready to advance - consider next stage")

        # Diversification
        owners = set(i['owner'] for i in ideas)
        if len(owners) == 1:
            recommendations.append("👥 Single owner: Consider distributing ownership for better scale")

        summary = f"""
        **Portfolio Health:** {'Strong' if sum(i['confidence_score'] for i in ideas) / len(ideas) >= 60 else 'Needs Attention'}

        - {len(ideas)} total ideas across {len(stage_dist)} stages
        - {len(high_confidence)} high-confidence ideas ready to scale
        - {len(at_risk)} ideas requiring risk mitigation
        """

        risk_analysis = f"""
        **Risk Profile:** {'High' if len(at_risk) > len(ideas) * 0.3 else 'Moderate' if len(at_risk) > 0 else 'Low'}

        Most common risks: {', '.join(set(i.get('risk_flags', '').split(',')[0].strip() for i in at_risk if i.get('risk_flags'))[:3]) if at_risk else 'None identified'}
        """

        return {
            'summary': summary,
            'recommendations': recommendations,
            'risk_analysis': risk_analysis,
            'using_ai': False
        }

    def _generate_openai_insights(self, ideas, metrics):
        """Generate insights using OpenAI GPT"""

        # Prepare context for GPT
        context = f"""
        Analyze this startup portfolio:

        Total Ideas: {metrics['total']}
        Average Confidence: {metrics['avg_confidence']:.0f}%
        High Confidence (≥70%): {metrics['high_confidence_count']}
        Low Confidence (<40%): {metrics['low_confidence_count']}
        At Risk: {metrics['at_risk_count']}

        Stage Distribution: {metrics['stage_distribution']}

        Ideas:
        """

        for idea in ideas[:5]:  # Limit to prevent token overflow
            context += f"\n- {idea['name']} ({idea['stage']}, {idea['confidence_score']}% confidence)"
            if idea.get('risk_flags'):
                context += f" - Risks: {idea['risk_flags']}"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a venture capital advisor analyzing a startup portfolio."},
                    {"role": "user", "content": f"{context}\n\nProvide: 1) Portfolio summary, 2) Top 3-5 recommendations, 3) Risk analysis"}
                ],
                max_tokens=500,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content

            # Parse response (simple split, could be improved)
            sections = ai_response.split('\n\n')

            return {
                'summary': sections[0] if len(sections) > 0 else "Portfolio analysis complete",
                'recommendations': [r.strip() for r in sections[1].split('\n') if r.strip()] if len(sections) > 1 else [],
                'risk_analysis': sections[2] if len(sections) > 2 else "Risk assessment pending",
                'using_ai': True
            }

        except Exception as e:
            # Fallback to rule-based if OpenAI fails
            print(f"OpenAI error: {e}")
            return self._generate_rule_based_insights(ideas,
                [i for i in ideas if i.get('risk_flags')],
                [i for i in ideas if i['confidence_score'] >= 70],
                [i for i in ideas if i['confidence_score'] < 40],
                metrics['stage_distribution'])

    def generate_offer_insights(self, offers: List[Dict[str, Any]]) -> str:
        """Generate insights about cohort offers"""

        if not offers:
            return "No offers to analyze yet. Add your first cohort offer!"

        high_scoring = [o for o in offers if (o.get('ai_score') or 0) >= 70]
        go_offers = [o for o in offers if o.get('go_no_go') == 'go']

        insights = []

        if len(high_scoring) > 0:
            insights.append(f"🚀 {len(high_scoring)} high-scoring offers ready for launch")

        if len(go_offers) == 0:
            insights.append("⏸️ No offers approved for launch - review pending offers")

        avg_ai_score = sum(o.get('ai_score', 0) for o in offers) / len(offers)
        if avg_ai_score >= 70:
            insights.append(f"✨ Strong portfolio average: {avg_ai_score:.0f} AI score")
        else:
            insights.append(f"📊 Portfolio needs refinement: {avg_ai_score:.0f} average AI score")

        return "\n".join(insights) if insights else "Portfolio looks balanced"

    def generate_energy_insights(self, entries: List[Dict[str, Any]]) -> str:
        """Generate insights about energy tracking"""

        if not entries or len(entries) < 7:
            return "Track at least 7 days to generate meaningful insights"

        scores = [e['energy_score'] for e in entries]
        avg_score = sum(scores) / len(scores)
        recent_7 = scores[:7]
        avg_recent = sum(recent_7) / 7

        recovery_days = sum(1 for e in entries if e['recovery_block'])

        insights = []

        # Trend analysis
        if avg_recent > avg_score:
            insights.append(f"📈 Improving: Recent 7-day average ({avg_recent:.1f}) above overall ({avg_score:.1f})")
        elif avg_recent < avg_score:
            insights.append(f"📉 Declining: Recent 7-day average ({avg_recent:.1f}) below overall ({avg_score:.1f})")
        else:
            insights.append(f"➡️ Stable: Consistent energy around {avg_score:.1f}/10")

        # Recovery analysis
        recovery_rate = recovery_days / len(entries)
        if recovery_rate < 0.15:  # Less than 1 day per week
            insights.append(f"⚠️ Low recovery: Only {recovery_days} recovery days in {len(entries)} days - consider more rest")
        else:
            insights.append(f"✅ Good recovery balance: {recovery_days} recovery days")

        # Energy level assessment
        if avg_score >= 7:
            insights.append("🔋 Excellent energy levels - sustain your habits!")
        elif avg_score >= 5:
            insights.append("⚡ Moderate energy - identify what boosts your score")
        else:
            insights.append("🪫 Low energy pattern - prioritize recovery and sleep")

        return "\n".join(insights)


# Global instance
ai_insights = AIInsights()
